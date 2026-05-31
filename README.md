# NVD Offline Package Audit

ابزاری برای بررسی آفلاین پکیج‌های نصب‌شده لینوکس و تولید لیست اولیه CVE بر اساس CPE و فیدهای محلی NVD.

این ابزار برای محیط‌هایی مناسب است که سرورها اینترنت ندارند یا اتصال مستقیم به سرویس‌های آنلاین مجاز نیست. ورودی یک فایل متنی از لیست پکیج‌هاست و خروجی به‌صورت Excel و CSV تولید می‌شود.

```text
Package List → CPE Mapping → Local NVD Feeds → CVE Report
```

## قابلیت‌ها

- اجرای آفلاین بعد از آماده‌سازی دیتابیس‌ها
- بدون نیاز به NVD API Key
- دریافت ورودی از فایل TXT
- پشتیبانی از خروجی `dpkg-query`
- پشتیبانی از خروجی `rpm`
- نگاشت Package به CPE با `cpe_search`
- جستجوی CVE از روی NVD JSON feeds به‌صورت local
- خروجی Excel و CSV
- ساخت cache برای اجرای سریع‌تر دفعات بعد

## نصب

```bash
apt update
apt install -y python3 python3-pip python3-venv curl gzip

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## آماده‌سازی دیتابیس‌ها

دانلود دیتابیس CPE:

```bash
cpe_search -d
```

دانلود فیدهای NVD:

```bash
mkdir -p nvd-feeds
cd nvd-feeds

for y in $(seq 2002 $(date +%Y)); do
  echo "[+] Downloading $y"
  curl -L -O "https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-${y}.json.gz"
done

gzip -t *.json.gz
cd ..
```

بعد از این مرحله، اجرای ابزار نیازی به اینترنت ندارد.

## گرفتن لیست پکیج‌ها

Debian / Ubuntu:

```bash
dpkg-query -W -f='${binary:Package} ${Version}\n' > packages_ubuntu.txt
```

RPM-based systems:

```bash
rpm -qa --queryformat '%{NAME} %{VERSION}-%{RELEASE}\n' > packages_rpm.txt
```

## اجرا

تست با چند پکیج:

```bash
python3 package_to_cve_offline.py \
  -i packages_ubuntu.txt \
  -o test_report.xlsx \
  --feeds ./nvd-feeds \
  --limit 10
```

اجرای کامل:

```bash
python3 package_to_cve_offline.py \
  -i packages_ubuntu.txt \
  -o report.xlsx \
  --feeds ./nvd-feeds
```

برای فایل RPM:

```bash
python3 package_to_cve_offline.py \
  -i packages_rpm.txt \
  -o rpm_report.xlsx \
  --feeds ./nvd-feeds
```

## خروجی

ابزار دو فایل خروجی تولید می‌کند:

```text
report.xlsx
report.csv
```

ستون‌های اصلی خروجی:

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
Published
Last Modified
CWE
Description
References
Matched NVD Criteria
CPE
Raw Package Line
```

## وضعیت‌ها

```text
CVE_FOUND      CVE احتمالی برای پکیج پیدا شده است
NO_CVE_FOUND   CPE پیدا شده ولی CVE مرتبط پیدا نشده است
NO_CPE_FOUND   CPE مناسبی برای پکیج پیدا نشده است
```

## محدودیت

این ابزار فقط بر اساس نام و نسخه پکیج کار می‌کند. در توزیع‌های لینوکسی ممکن است patchهای امنیتی به‌صورت backport اعمال شده باشند و نسخه upstream تغییر نکرده باشد. بنابراین خروجی ابزار باید به‌عنوان لیست اولیه و قابل بررسی استفاده شود، نه گزارش قطعی آسیب‌پذیری.

برای نتیجه نهایی، خروجی باید با advisory رسمی توزیع یا vendor مقایسه شود.

توضیحات بیشتر در:

```text
docs/offline-workflow.md
```
