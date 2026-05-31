# NVD Offline Package Audit

Offline Linux package-to-CVE audit tool using local CPE database and local NVD JSON feeds.

This tool takes a text file containing installed Linux packages, detects possible CPE matches, checks them against local NVD CVE feeds, and generates Excel and CSV reports.

It is designed for environments where servers do not have internet access or are not allowed to connect to external services.

```text
Package List → CPE Detection → Local NVD Feeds → CVE Report
```

---

## Features

```text
- Fully offline execution after database preparation
- No NVD API key required
- No internet access required during report generation
- Supports Debian/Ubuntu package lists
- Supports RPM-based package lists
- Uses local cpe_search database
- Uses local NVD JSON feeds
- Generates Excel and CSV reports
- Builds a local cache for faster future runs
```

---

## Important Note

This tool does not perform active vulnerability scanning.

It only compares installed package names and versions with local CPE and NVD data. The result should be treated as an initial candidate CVE list, not as a final vulnerability assessment.

Linux distributions may backport security patches without changing the upstream software version. Because of that, false positives are possible.

Final validation should be done using official vendor advisories such as Ubuntu USN, Debian Security Tracker, Red Hat RHSA/OVAL, SUSE advisories, Oracle Linux advisories, or other vendor-specific sources.

---

## Requirements

```bash
apt update
apt install -y python3 python3-pip python3-venv curl gzip
```

Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt`:

```text
pandas
openpyxl
tqdm
cpe-search
```

If `cpe-search` is not available from PyPI:

```bash
pip install git+https://github.com/ra1nb0rn/cpe_search.git
```

---

## Prepare Local CPE Database

This step requires internet access once.

```bash
cpe_search -d
```

Test:

```bash
cpe_search -q "openssl 3.0.13" -n 3 --no-progress
```

After this step, CPE detection can work offline.

---

## Prepare Local NVD Feeds

This step requires internet access once.

```bash
mkdir -p nvd-feeds
cd nvd-feeds
```

Download NVD JSON 2.0 feeds:

```bash
for y in $(seq 2002 $(date +%Y)); do
  echo "[+] Downloading $y"
  curl -L -O "https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-${y}.json.gz"
done
```

Verify files:

```bash
gzip -t *.json.gz
```

If there is no output, the files are valid.

---

## Collect Package List

Debian / Ubuntu:

```bash
dpkg-query -W -f='${binary:Package} ${Version}\n' > packages_ubuntu.txt
```

RPM-based systems:

```bash
rpm -qa --queryformat '%{NAME} %{VERSION}-%{RELEASE}\n' > packages_rpm.txt
```

Example input:

```text
sudo 1.9.15p5-3ubuntu5
openssl 3.0.13-0ubuntu3.5
bash 5.2.21-2ubuntu4
```

---

## Test Run

```bash
python3 package_to_cve_offline.py \
  -i packages_ubuntu.txt \
  -o test_report.xlsx \
  --feeds ./nvd-feeds \
  --limit 10
```

The first run may take a few minutes because the tool builds a local NVD index.

Cache file:

```text
nvd-feeds/nvd_offline_index.pkl
```

---

## Full Run

Ubuntu / Debian:

```bash
python3 package_to_cve_offline.py \
  -i packages_ubuntu.txt \
  -o ubuntu_report.xlsx \
  --feeds ./nvd-feeds
```

RPM-based systems:

```bash
python3 package_to_cve_offline.py \
  -i packages_rpm.txt \
  -o rpm_report.xlsx \
  --feeds ./nvd-feeds
```

Output files:

```text
ubuntu_report.xlsx
ubuntu_report.csv
```

---

## Output Columns

```text
Status
Package
Installed Version
Search Version
CPE Vendor
CPE Product
CPE Version
Match Type
CVE
Severity
CVSS
CVSS Vector
Published
Last Modified
CWE
Description
References
Matched NVD Criteria
CPE
Raw Package Line
```

---

## Status Values

```text
CVE_FOUND      Possible CVE was found
NO_CVE_FOUND   CPE was found, but no related CVE was found
NO_CPE_FOUND   No suitable CPE was found for the package
```

---

## Match Types

```text
EXACT
CPE_EXACT
PARTIAL
RANGE
CANDIDATE
```

`PARTIAL` and `CANDIDATE` results should be reviewed manually.

---

## Update Local Database

To update local NVD feeds:

```bash
cd nvd-feeds

for y in $(seq 2002 $(date +%Y)); do
  echo "[+] Updating $y"
  curl -L -O "https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-${y}.json.gz"
done

gzip -t *.json.gz
rm -f nvd_offline_index.pkl
```

The next run will rebuild the local index.

---

## Limitations

```text
- Does not scan the network
- Does not check open ports
- Does not check whether a service is running
- Does not confirm exploitability
- Does not validate vendor backported patches
- Does not replace Nessus, OpenVAS, Qualys, OVAL, RHSA, USN or manual review
```

---

## Minimal Usage

```bash
python3 package_to_cve_offline.py -i packages_ubuntu.txt -o report.xlsx --feeds ./nvd-feeds
```

After preparing local databases, this command runs without internet access.

---
