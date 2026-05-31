# Offline Workflow

این سند روند کامل آماده‌سازی و اجرای ابزار را توضیح می‌دهد. README اصلی فقط دستورات ضروری را نگه می‌دارد.

## 1. هدف

در بعضی پروژه‌های ممیزی، سیستم‌های هدف اینترنت ندارند یا اجازه اتصال مستقیم به NVD، Repositoryها یا سرویس‌های آنلاین وجود ندارد. در این حالت می‌توان لیست پکیج‌ها را از سیستم هدف گرفت و روی یک سیستم جداگانه که دیتابیس‌های لازم را دارد، تحلیل آفلاین انجام داد.

روند کار:

```text
1. Collect package list from target
2. Map package/version to CPE using local cpe_search DB
3. Search local NVD JSON feeds for matching CVEs
4. Generate Excel/CSV report
```

## 2. دیتابیس‌های مورد نیاز

دو دیتابیس محلی لازم است.

### CPE database

برای تبدیل package به CPE استفاده می‌شود.

```bash
cpe_search -d
```

بعد از دانلود، `cpe_search` می‌تواند بدون اینترنت کار کند.

تست:

```bash
cpe_search -q "openssl 3.0.13" -n 3 --no-progress
```

### NVD JSON feeds

برای جستجوی CVEها استفاده می‌شود.

```bash
mkdir -p nvd-feeds
cd nvd-feeds

for y in $(seq 2002 $(date +%Y)); do
  echo "[+] Downloading $y"
  curl -L -O "https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-${y}.json.gz"
done

gzip -t *.json.gz
```

اگر `gzip -t` خروجی نداشت، فایل‌ها سالم هستند.

## 3. گرفتن لیست پکیج از سیستم هدف

### Debian / Ubuntu

```bash
dpkg-query -W -f='${binary:Package} ${Version}\n' > packages_ubuntu.txt
```

نمونه:

```text
sudo 1.9.15p5-3ubuntu5
openssl 3.0.13-0ubuntu3.5
bash 5.2.21-2ubuntu4
```

### RPM-based systems

```bash
rpm -qa --queryformat '%{NAME} %{VERSION}-%{RELEASE}\n' > packages_rpm.txt
```

نمونه:

```text
sudo 1.8.29-10.el8
openssl 1.1.1k-12.el8
bash 4.4.20-5.el8
```

## 4. اجرای تست

اول با تعداد محدود اجرا شود تا فرمت فایل و دیتابیس‌ها بررسی شوند.

```bash
python3 package_to_cve_offline.py \
  -i packages_ubuntu.txt \
  -o test_report.xlsx \
  --feeds ./nvd-feeds \
  --limit 10
```

اجرای اول ممکن است زمان بیشتری بگیرد، چون ابزار از روی فیدهای NVD یک index محلی می‌سازد.

فایل cache:

```text
nvd-feeds/nvd_offline_index.pkl
```

در اجراهای بعدی، ابزار از همین cache استفاده می‌کند و سریع‌تر اجرا می‌شود.

## 5. اجرای کامل

```bash
python3 package_to_cve_offline.py \
  -i packages_ubuntu.txt \
  -o ubuntu_report.xlsx \
  --feeds ./nvd-feeds
```

یا برای RPM:

```bash
python3 package_to_cve_offline.py \
  -i packages_rpm.txt \
  -o rpm_report.xlsx \
  --feeds ./nvd-feeds
```

## 6. معنی Match Type

```text
EXACT       نسخه نصب‌شده با criteria در NVD تطابق مستقیم دارد
CPE_EXACT   نسخه CPE با criteria تطابق دارد
PARTIAL     تطابق نسبی نسخه تشخیص داده شده است
RANGE       نسخه داخل بازه versionStart/versionEnd قرار گرفته است
CANDIDATE   تطابق احتمالی است و باید دستی بررسی شود
```

موارد `CANDIDATE` و `PARTIAL` حتماً باید دستی بررسی شوند.

## 7. به‌روزرسانی دیتابیس

برای آپدیت فیدهای NVD:

```bash
cd nvd-feeds

for y in $(seq 2002 $(date +%Y)); do
  echo "[+] Updating $y"
  curl -L -O "https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-${y}.json.gz"
done

gzip -t *.json.gz
rm -f nvd_offline_index.pkl
```

بعد از حذف cache، اجرای بعدی index جدید می‌سازد.

## 8. نکات ممیزی

این ابزار نتیجه قطعی آسیب‌پذیری تولید نمی‌کند. خروجی آن یک candidate list است.

دلایل اصلی false positive:

```text
- backport شدن patchها در توزیع‌های لینوکسی
- تفاوت نسخه package با نسخه upstream
- خطای احتمالی در نگاشت package به CPE
- عمومی بودن داده‌های NVD نسبت به packageهای vendor-specific
```

برای نتیجه نهایی باید خروجی با منابع رسمی vendor بررسی شود، مثل:

```text
Ubuntu USN
Debian Security Tracker
Red Hat RHSA / OVAL
SUSE Advisories
Oracle Linux Advisories
EulerOS Advisories
```

## 9. فایل‌هایی که نباید commit شوند

```text
nvd-feeds/
*.json.gz
*.pkl
*.xlsx
*.csv
venv/
```
