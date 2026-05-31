#!/usr/bin/env python3
import argparse
import gzip
import json
import os
import pickle
import re
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd
from tqdm import tqdm


ARCH_SUFFIXES = [
    ".x86_64", ".i686", ".i386", ".noarch", ".aarch64",
    ".arm64", ".armv7hl", ".ppc64le", ".s390x"
]


def clean_version(version: str) -> str:
    if not version:
        return ""
    version = version.strip()
    version = version.split(":")[-1]
    version = version.split("-")[0]
    return version


def parse_package_line(line: str):
    original = line.strip()
    if not original or original.startswith("#"):
        return None

    # apt list format
    if "/" in original and "[installed" in original:
        parts = original.split()
        if len(parts) >= 2:
            name = parts[0].split("/")[0].strip()
            version = parts[1].strip()
            return {
                "package": name,
                "installed_version": version,
                "search_version": clean_version(version),
                "raw_line": original,
            }

    # package version
    parts = original.split()
    if len(parts) >= 2:
        name = parts[0].strip()
        version = parts[1].strip()
        return {
            "package": name,
            "installed_version": version,
            "search_version": clean_version(version),
            "raw_line": original,
        }

    # rpm -qa format
    rpm_line = original
    for arch in ARCH_SUFFIXES:
        if rpm_line.endswith(arch):
            rpm_line = rpm_line[:-len(arch)]
            break

    rpm_parts = rpm_line.rsplit("-", 2)
    if len(rpm_parts) == 3:
        name = rpm_parts[0]
        version = rpm_parts[1] + "-" + rpm_parts[2]
        return {
            "package": name,
            "installed_version": version,
            "search_version": clean_version(version),
            "raw_line": original,
        }

    return {
        "package": original,
        "installed_version": "",
        "search_version": "",
        "raw_line": original,
    }


def load_packages(input_file):
    packages = []
    seen = set()

    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            item = parse_package_line(line)
            if not item:
                continue
            key = (item["package"], item["installed_version"])
            if key not in seen:
                seen.add(key)
                packages.append(item)

    return packages


def parse_cpe(cpe: str):
    parts = cpe.split(":")
    return {
        "part": parts[2] if len(parts) > 2 else "",
        "vendor": parts[3] if len(parts) > 3 else "",
        "product": parts[4] if len(parts) > 4 else "",
        "version": parts[5] if len(parts) > 5 else "",
    }


def run_cpe_search(package_name, version, top_n=2):
    query = f"{package_name} {version}".strip()
    cmd = ["cpe_search", "-q", query, "-n", str(top_n), "--no-progress"]

    try:
        result = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=60,
        )

        output = (result.stdout or "") + "\n" + (result.stderr or "")
        cpes = re.findall(r"cpe:2\.3:[aho]:[^\s\"']+", output)

        cleaned = []
        for cpe in cpes:
            cpe = cpe.strip().rstrip(",;")
            if cpe not in cleaned:
                cleaned.append(cpe)

        return cleaned, output.strip()

    except Exception as e:
        return [], f"cpe_search_error: {type(e).__name__}: {e}"


def extract_nodes(nodes):
    matches = []

    for node in nodes or []:
        for cpe_match in node.get("cpeMatch", []):
            matches.append(cpe_match)

        if "children" in node:
            matches.extend(extract_nodes(node.get("children", [])))

    return matches


def get_cvss(cve):
    metrics = cve.get("metrics", {})

    for key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
        if key in metrics and metrics[key]:
            metric = metrics[key][0]
            cvss_data = metric.get("cvssData", {})
            return {
                "score": cvss_data.get("baseScore", ""),
                "severity": cvss_data.get("baseSeverity", metric.get("baseSeverity", "")),
                "vector": cvss_data.get("vectorString", ""),
                "source": key,
            }

    return {"score": "", "severity": "", "vector": "", "source": ""}


def get_english_description(cve):
    for d in cve.get("descriptions", []):
        if d.get("lang") == "en":
            return d.get("value", "").replace("\n", " ").replace("\r", " ")
    return ""


def get_weakness(cve):
    values = []
    for weakness in cve.get("weaknesses", []):
        for desc in weakness.get("description", []):
            if desc.get("lang") == "en":
                values.append(desc.get("value", ""))
    return ", ".join(sorted(set(values)))


def get_references(cve, limit=8):
    refs = cve.get("references", {}).get("referenceData", [])
    return "\n".join([r.get("url", "") for r in refs[:limit]])


def version_to_tuple(v):
    if not v:
        return ()
    nums = re.findall(r"\d+", v)
    return tuple(int(x) for x in nums[:6])


def version_compare(a, b):
    ta = version_to_tuple(a)
    tb = version_to_tuple(b)

    if not ta or not tb:
        return None

    max_len = max(len(ta), len(tb))
    ta = ta + (0,) * (max_len - len(ta))
    tb = tb + (0,) * (max_len - len(tb))

    if ta < tb:
        return -1
    if ta > tb:
        return 1
    return 0


def version_in_range(version, cpe_match):
    """
    Conservative candidate matching:
    - If criteria has exact version and it matches installed/search version: YES
    - If NVD has versionStart/versionEnd fields: compare numerically where possible
    - If cannot decide safely: return UNKNOWN/CANDIDATE
    """
    if not version:
        return "UNKNOWN"

    version = clean_version(version)

    start_inc = cpe_match.get("versionStartIncluding")
    start_exc = cpe_match.get("versionStartExcluding")
    end_inc = cpe_match.get("versionEndIncluding")
    end_exc = cpe_match.get("versionEndExcluding")

    checks = []

    if start_inc:
        cmp = version_compare(version, start_inc)
        if cmp is not None:
            checks.append(cmp >= 0)

    if start_exc:
        cmp = version_compare(version, start_exc)
        if cmp is not None:
            checks.append(cmp > 0)

    if end_inc:
        cmp = version_compare(version, end_inc)
        if cmp is not None:
            checks.append(cmp <= 0)

    if end_exc:
        cmp = version_compare(version, end_exc)
        if cmp is not None:
            checks.append(cmp < 0)

    if checks:
        return "YES" if all(checks) else "NO"

    return "UNKNOWN"


def build_nvd_index(feeds_dir):
    feeds_dir = Path(feeds_dir)
    cache_file = feeds_dir / "nvd_offline_index.pkl"

    if cache_file.exists():
        print(f"[+] Loading cached NVD index: {cache_file}")
        with open(cache_file, "rb") as f:
            return pickle.load(f)

    print("[+] Building offline NVD index. First run may take a few minutes...")

    index = {}
    feed_files = sorted(feeds_dir.glob("nvdcve-2.0-*.json.gz"))

    if not feed_files:
        raise FileNotFoundError(f"No NVD feed files found in: {feeds_dir}")

    for feed_file in tqdm(feed_files, desc="Loading NVD feeds"):
        with gzip.open(feed_file, "rt", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)

        for item in data.get("vulnerabilities", []):
            cve = item.get("cve", {})
            cve_id = cve.get("id", "")

            for config in cve.get("configurations", []):
                matches = extract_nodes(config.get("nodes", []))

                for m in matches:
                    if not m.get("vulnerable", False):
                        continue

                    criteria = m.get("criteria", "")
                    if not criteria.startswith("cpe:2.3:"):
                        continue

                    cpe_info = parse_cpe(criteria)
                    key = (
                        cpe_info["part"],
                        cpe_info["vendor"],
                        cpe_info["product"],
                    )

                    record = {
                        "cve_id": cve_id,
                        "cve": cve,
                        "criteria": criteria,
                        "criteria_version": cpe_info["version"],
                        "match": m,
                    }

                    index.setdefault(key, []).append(record)

    with open(cache_file, "wb") as f:
        pickle.dump(index, f)

    print(f"[+] Cache saved: {cache_file}")
    return index


def match_cves_for_cpe(index, cpe, installed_version):
    cpe_info = parse_cpe(cpe)
    key = (cpe_info["part"], cpe_info["vendor"], cpe_info["product"])
    candidates = index.get(key, [])

    results = []

    installed_clean = clean_version(installed_version)
    cpe_version = cpe_info["version"]

    for rec in candidates:
        criteria_version = rec["criteria_version"]
        m = rec["match"]

        match_status = "CANDIDATE"

        if criteria_version and criteria_version != "*":
            if installed_clean and installed_clean == criteria_version:
                match_status = "EXACT"
            elif cpe_version and cpe_version == criteria_version:
                match_status = "CPE_EXACT"
            elif installed_clean and (
                installed_clean.startswith(criteria_version) or criteria_version.startswith(installed_clean)
            ):
                match_status = "PARTIAL"
            else:
                continue
        else:
            range_status = version_in_range(installed_clean or cpe_version, m)
            if range_status == "NO":
                continue
            if range_status == "YES":
                match_status = "RANGE"
            else:
                match_status = "CANDIDATE"

        results.append((rec, match_status))

    return results


def make_no_result_row(pkg, status, note="", cpe=""):
    cpe_info = parse_cpe(cpe) if cpe else {"vendor": "", "product": "", "version": ""}

    return {
        "Status": status,
        "Package": pkg["package"],
        "Installed Version": pkg["installed_version"],
        "Search Version": pkg["search_version"],
        "CPE Vendor": cpe_info["vendor"],
        "CPE Product": cpe_info["product"],
        "CPE Version": cpe_info["version"],
        "Match Type": "",
        "CVE": "",
        "Severity": "",
        "CVSS": "",
        "CVSS Vector": "",
        "CVSS Source": "",
        "Published": "",
        "Last Modified": "",
        "CWE": "",
        "Description": note,
        "References": "",
        "Matched NVD Criteria": "",
        "CPE": cpe,
        "Raw Package Line": pkg["raw_line"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Offline Package to CVE mapper using local cpe_search DB and local NVD JSON feeds."
    )

    parser.add_argument("-i", "--input", required=True, help="Input package TXT file")
    parser.add_argument("-o", "--output", default="offline_report.xlsx", help="Output Excel file")
    parser.add_argument("--feeds", default="./nvd-feeds", help="Directory containing NVD nvdcve-2.0-YYYY.json.gz files")
    parser.add_argument("--top-cpe", type=int, default=2, help="Top CPE matches per package")
    parser.add_argument("--limit", type=int, default=0, help="Limit packages for test. 0 means all.")

    args = parser.parse_args()

    packages = load_packages(args.input)
    if args.limit and args.limit > 0:
        packages = packages[:args.limit]

    print("=" * 70)
    print("Offline Package to CVE Audit")
    print("=" * 70)
    print(f"Input file: {args.input}")
    print(f"Feeds dir:  {args.feeds}")
    print(f"Packages:   {len(packages)}")
    print(f"Output:     {args.output}")
    print("=" * 70)

    nvd_index = build_nvd_index(args.feeds)

    rows = []
    cpe_cache = {}

    for pkg in tqdm(packages, desc="Processing packages"):
        cpe_key = f"{pkg['package']} {pkg['search_version']}"

        if cpe_key in cpe_cache:
            cpes, debug = cpe_cache[cpe_key]
        else:
            cpes, debug = run_cpe_search(pkg["package"], pkg["search_version"], args.top_cpe)
            cpe_cache[cpe_key] = (cpes, debug)

        if not cpes:
            rows.append(make_no_result_row(
                pkg,
                "NO_CPE_FOUND",
                note=f"No CPE found by cpe_search. Debug: {debug[:500]}"
            ))
            continue

        any_cve = False

        for cpe in cpes[:args.top_cpe]:
            matched = match_cves_for_cpe(nvd_index, cpe, pkg["installed_version"])

            if not matched:
                rows.append(make_no_result_row(pkg, "NO_CVE_FOUND", cpe=cpe))
                continue

            any_cve = True
            cpe_info = parse_cpe(cpe)

            for rec, match_type in matched:
                cve = rec["cve"]
                cvss = get_cvss(cve)

                rows.append({
                    "Status": "CVE_FOUND",
                    "Package": pkg["package"],
                    "Installed Version": pkg["installed_version"],
                    "Search Version": pkg["search_version"],
                    "CPE Vendor": cpe_info["vendor"],
                    "CPE Product": cpe_info["product"],
                    "CPE Version": cpe_info["version"],
                    "Match Type": match_type,
                    "CVE": cve.get("id", ""),
                    "Severity": cvss["severity"],
                    "CVSS": cvss["score"],
                    "CVSS Vector": cvss["vector"],
                    "CVSS Source": cvss["source"],
                    "Published": cve.get("published", ""),
                    "Last Modified": cve.get("lastModified", ""),
                    "CWE": get_weakness(cve),
                    "Description": get_english_description(cve),
                    "References": get_references(cve),
                    "Matched NVD Criteria": rec["criteria"],
                    "CPE": cpe,
                    "Raw Package Line": pkg["raw_line"],
                })

    df = pd.DataFrame(rows)

    if not df.empty:
        severity_order = {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 4,
            "": 99,
        }

        df["Severity Order"] = df["Severity"].map(severity_order).fillna(99)
        df = df.sort_values(
            by=["Severity Order", "CVSS", "Package", "CVE"],
            ascending=[True, False, True, True]
        )
        df = df.drop(columns=["Severity Order"])

    csv_output = args.output.replace(".xlsx", ".csv")

    df.to_csv(csv_output, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(args.output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Findings", index=False)

        summary = pd.DataFrame([
            {"Metric": "Generated At", "Value": datetime.now().isoformat(timespec="seconds")},
            {"Metric": "Mode", "Value": "OFFLINE"},
            {"Metric": "Input File", "Value": args.input},
            {"Metric": "NVD Feeds Dir", "Value": args.feeds},
            {"Metric": "Packages Loaded", "Value": len(packages)},
            {"Metric": "Rows Generated", "Value": len(df)},
            {"Metric": "Top CPE Per Package", "Value": args.top_cpe},
        ])

        summary.to_excel(writer, sheet_name="Summary", index=False)

        if not df.empty:
            counts = df.groupby(["Status", "Severity"], dropna=False).size().reset_index(name="Count")
            counts.to_excel(writer, sheet_name="Counts", index=False)

    print("=" * 70)
    print("DONE - OFFLINE REPORT CREATED")
    print(f"Excel: {args.output}")
    print(f"CSV:   {csv_output}")
    print("=" * 70)


if __name__ == "__main__":
    main()
