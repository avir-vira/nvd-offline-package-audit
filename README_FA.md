# بررسی آفلاین CVE پکیج‌های لینوکس

این پروژه یک ابزار آفلاین برای بررسی لیست پکیج‌های نصب‌شده روی سیستم‌های لینوکسی و استخراج CVEهای احتمالی مرتبط با آن‌هاست.

ابزار بدون نیاز به اتصال آنلاین به NVD API کار می‌کند و برای محیط‌هایی مناسب است که سیستم‌ها دسترسی اینترنت ندارند یا اتصال مستقیم آن‌ها به اینترنت مجاز نیست.

فرایند کلی ابزار:

```text
Package List TXT
        ↓
CPE Detection با دیتابیس محلی cpe_search
        ↓
جستجو در فایل‌های آفلاین NVD JSON
        ↓
تولید گزارش Excel و CSV
```

---

## هدف پروژه

در بسیاری از پروژه‌های ممیزی امنیتی، مخصوصاً در محیط‌های عملیاتی، بانکی، تلکام، دیتاسنترهای ایزوله و شبکه‌های Air-Gapped، امکان نصب و اجرای ابزارهای آنلاین یا اتصال مستقیم سرورها به اینترنت وجود ندارد.

در چنین شرایطی معمولاً فقط می‌توان از سیستم هدف یک لیست پکیج گرفت و آن را برای بررسی آفلاین تحلیل کرد.

این ابزار دقیقاً برای همین سناریو طراحی شده است:

```text
گرفتن لیست پکیج‌ها از سیستم هدف
انتقال فایل TXT به سیستم تحلیل‌گر
اجرای ابزار به‌صورت آفلاین
تولید گزارش اولیه CVE
```

---

## این ابزار چه کاری انجام می‌دهد؟

ابزار از روی نام و نسخه پکیج، ابتدا CPEهای احتمالی را پیدا می‌کند و سپس CVEهای مرتبط را از دیتابیس محلی NVD استخراج می‌کند.

به‌طور خلاصه:

```text
Package Name + Package Version
        ↓
Possible CPE
        ↓
Related CVEs
        ↓
Excel / CSV Report
```

نمونه:

```text
openssl 3.0.13-0ubuntu3.5
        ↓
cpe:2.3:a:openssl:openssl:3.0.13:*:*:*:*:*:*:*
        ↓
CVE list
```

---

## این ابزار چه کاری انجام نمی‌دهد؟

این ابزار اسکنر آسیب‌پذیری نیست.

موارد زیر را انجام نمی‌دهد:

```text
اسکن شبکه
اسکن پورت
بررسی فعال بودن سرویس
بررسی تنظیمات سرویس
بررسی Exploitability
بررسی Exposure واقعی
بررسی Patchهای Backport شده Vendor
اجرای تست نفوذ
جایگزینی Nessus، OpenVAS، Qualys یا ابزارهای VA
```

خروجی ابزار باید به‌عنوان یک فهرست اولیه از CVEهای احتمالی استفاده شود، نه گزارش قطعی آسیب‌پذیری.

---

## نکته مهم درباره False Positive

در توزیع‌های لینوکسی مثل Ubuntu، Debian، RHEL، CentOS، Rocky Linux، AlmaLinux، Oracle Linux، EulerOS و SUSE ممکن است پچ‌های امنیتی به‌صورت Backport اعمال شده باشند.

یعنی ممکن است نسخه نرم‌افزار ظاهراً قدیمی باشد، اما اصلاح امنیتی روی همان نسخه اعمال شده باشد.

بنابراین ممکن است ابزار برای یک پکیج CVE نشان دهد، در حالی که آن CVE توسط Vendor پچ شده باشد.

برای تأیید نهایی باید خروجی با منابع رسمی Vendor بررسی شود؛ مثل:

```text
Ubuntu Security Notices - USN
Debian Security Tracker
Red Hat RHSA / OVAL
SUSE Security Advisories
Oracle Linux Security Advisories
EulerOS Security Advisories
Vendor-specific advisories
```

---

## قابلیت‌ها

```text
اجرای آفلاین بعد از آماده‌سازی دیتابیس‌ها
بدون نیاز به NVD API Key
بدون ارسال درخواست به NVD API هنگام اجرای گزارش
پشتیبانی از لیست پکیج‌های Debian / Ubuntu
پشتیبانی از لیست پکیج‌های RPM-based
استفاده از دیتابیس محلی cpe_search
استفاده از فایل‌های محلی NVD JSON 2.0
تولید خروجی Excel
تولید خروجی CSV
ساخت Cache محلی برای اجرای سریع‌تر در دفعات بعد
امکان اجرای محدود برای تست اولیه
```

---

## ساختار پیشنهادی پروژه

```text
nvd-offline-package-audit/
│
├── package_to_cve_offline.py
├── requirements.txt
├── README.md
├── README_FA.md
├── .gitignore
│
├── docs/
│   └── offline-workflow.md
│
└── examples/
    ├── packages_ubuntu_sample.txt
    └── packages_rpm_sample.txt
```

فایل‌های زیر نباید داخل GitHub قرار بگیرند:

```text
venv/
nvd-feeds/
*.json.gz
*.pkl
*.xlsx
*.csv
packages_ubuntu.txt واقعی
packages_rpm.txt واقعی
```

دلیلش این است که دیتابیس‌های NVD حجیم هستند و فایل‌های خروجی یا لیست پکیج واقعی ممکن است اطلاعات سیستم هدف را افشا کنند.

---

## پیش‌نیازها

برای اجرای ابزار به Python و چند کتابخانه نیاز است.

روی Ubuntu یا WSL:

```bash
apt update
apt install -y python3 python3-pip python3-venv curl gzip
```

ساخت محیط مجازی Python:

```bash
python3 -m venv venv
source venv/bin/activate
```

نصب وابستگی‌ها:

```bash
pip install -r requirements.txt
```

محتوای فایل `requirements.txt`:

```text
pandas
openpyxl
tqdm
cpe-search
```

اگر نصب `cpe-search` از PyPI انجام نشد، می‌توان آن را مستقیم از GitHub نصب کرد:

```bash
pip install git+https://github.com/ra1nb0rn/cpe_search.git
```

---

## مرحله 1 — آماده‌سازی دیتابیس محلی CPE

این مرحله فقط یک بار به اینترنت نیاز دارد.

```bash
cpe_search -d
```

بعد از اجرا، دیتابیس محلی CPE دانلود می‌شود.

برای تست:

```bash
cpe_search -q "openssl 3.0.13" -n 3 --no-progress
```

اگر خروجی CPE نمایش داده شد، این بخش درست کار می‌کند.

بعد از این مرحله، بخش تشخیص CPE می‌تواند آفلاین اجرا شود.

---

## مرحله 2 — آماده‌سازی فایل‌های آفلاین NVD

این مرحله هم فقط یک بار به اینترنت نیاز دارد.

داخل مسیر پروژه:

```bash
mkdir -p nvd-feeds
cd nvd-feeds
```

دانلود فایل‌های سالانه NVD JSON 2.0:

```bash
for y in $(seq 2002 $(date +%Y)); do
  echo "[+] Downloading $y"
  curl -L -O "https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-${y}.json.gz"
done
```

بررسی سلامت فایل‌ها:

```bash
gzip -t *.json.gz
```

اگر خروجی خاصی نمایش داده نشد، فایل‌ها سالم هستند.

نمونه فایل‌های مورد انتظار:

```text
nvdcve-2.0-2002.json.gz
nvdcve-2.0-2003.json.gz
nvdcve-2.0-2004.json.gz
...
nvdcve-2.0-2026.json.gz
```

بعد از این مرحله، ابزار برای استخراج CVE نیازی به اینترنت ندارد.

---

## مرحله 3 — گرفتن لیست پکیج‌ها از سیستم هدف

### Debian / Ubuntu

روی سیستم هدف:

```bash
dpkg-query -W -f='${binary:Package} ${Version}\n' > packages_ubuntu.txt
```

نمونه خروجی:

```text
sudo 1.9.15p5-3ubuntu5
openssl 3.0.13-0ubuntu3.5
bash 5.2.21-2ubuntu4
```

---

### RHEL / CentOS / Rocky / AlmaLinux / Oracle Linux / EulerOS

روی سیستم هدف:

```bash
rpm -qa --queryformat '%{NAME} %{VERSION}-%{RELEASE}\n' > packages_rpm.txt
```

نمونه خروجی:

```text
sudo 1.8.29-10.el8
openssl 1.1.1k-12.el8
bash 4.4.20-5.el8
```

---

## مرحله 4 — اجرای تست اولیه

قبل از اجرای کامل، بهتر است ابزار را روی تعداد کمی پکیج تست کنید.

برای Ubuntu / Debian:

```bash
python3 package_to_cve_offline.py \
  -i packages_ubuntu.txt \
  -o test_report.xlsx \
  --feeds ./nvd-feeds \
  --limit 10
```

برای RPM-based:

```bash
python3 package_to_cve_offline.py \
  -i packages_rpm.txt \
  -o test_report.xlsx \
  --feeds ./nvd-feeds \
  --limit 10
```

اجرای اول ممکن است چند دقیقه زمان ببرد، چون ابزار از روی فایل‌های NVD یک Index محلی می‌سازد.

بعد از اجرای اول، فایل Cache ساخته می‌شود:

```text
nvd-feeds/nvd_offline_index.pkl
```

در اجراهای بعدی ابزار سریع‌تر خواهد بود.

---

## مرحله 5 — اجرای کامل

برای Ubuntu / Debian:

```bash
python3 package_to_cve_offline.py \
  -i packages_ubuntu.txt \
  -o ubuntu_report.xlsx \
  --feeds ./nvd-feeds
```

برای RPM-based:

```bash
python3 package_to_cve_offline.py \
  -i packages_rpm.txt \
  -o rpm_report.xlsx \
  --feeds ./nvd-feeds
```

فایل‌های خروجی:

```text
ubuntu_report.xlsx
ubuntu_report.csv
```

یا:

```text
rpm_report.xlsx
rpm_report.csv
```

---

## پارامترهای اصلی ابزار

```text
-i / --input     مسیر فایل ورودی پکیج‌ها
-o / --output    نام فایل خروجی Excel
--feeds          مسیر پوشه فایل‌های NVD
--limit          محدود کردن تعداد پکیج‌ها برای تست
--top-cpe        تعداد CPEهای پیشنهادی برای هر پکیج
```

نمونه:

```bash
python3 package_to_cve_offline.py \
  -i packages_ubuntu.txt \
  -o report.xlsx \
  --feeds ./nvd-feeds \
  --limit 20 \
  --top-cpe 2
```

---

## ستون‌های خروجی Excel

گزارش Excel شامل ستون‌های زیر است:

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
CVSS Source
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

## توضیح ستون‌های مهم

### Package

نام پکیج استخراج‌شده از فایل ورودی.

### Installed Version

نسخه نصب‌شده پکیج، همان‌طور که در فایل ورودی آمده است.

### Search Version

نسخه ساده‌سازی‌شده برای جستجوی بهتر CPE.

مثلاً:

```text
3.0.13-0ubuntu3.5 → 3.0.13
```

### CPE Vendor / CPE Product / CPE Version

اطلاعات استخراج‌شده از CPE پیدا شده.

### CVE

شناسه CVE پیدا شده.

### Severity

شدت آسیب‌پذیری بر اساس داده‌های NVD.

### CVSS

امتیاز CVSS.

### Match Type

نوع تطبیق بین نسخه پکیج، CPE و داده‌های NVD.

### Matched NVD Criteria

معیار CPE ثبت‌شده در NVD که باعث پیدا شدن CVE شده است.

### Raw Package Line

خط خام فایل ورودی، برای Evidence و بررسی دستی.

---

## مقدارهای Status

```text
CVE_FOUND
NO_CVE_FOUND
NO_CPE_FOUND
```

توضیح:

```text
CVE_FOUND      CVE احتمالی برای پکیج پیدا شده است
NO_CVE_FOUND   CPE پیدا شده، اما CVE مرتبط در فایل‌های NVD پیدا نشده است
NO_CPE_FOUND   ابزار نتوانسته برای پکیج CPE مناسب پیدا کند
```

---

## مقدارهای Match Type

```text
EXACT
CPE_EXACT
PARTIAL
RANGE
CANDIDATE
```

توضیح:

```text
EXACT       نسخه نصب‌شده با معیار NVD مطابقت مستقیم دارد
CPE_EXACT   نسخه CPE با معیار NVD مطابقت دارد
PARTIAL     تطبیق نسبی بین نسخه‌ها وجود دارد
RANGE       نسخه داخل بازه آسیب‌پذیر ثبت‌شده در NVD قرار گرفته است
CANDIDATE   تطبیق احتمالی است و باید دستی بررسی شود
```

موارد `PARTIAL` و `CANDIDATE` باید با دقت بیشتری بررسی شوند.

---

## به‌روزرسانی دیتابیس محلی

برای به‌روزرسانی دیتابیس NVD:

```bash
cd nvd-feeds

for y in $(seq 2002 $(date +%Y)); do
  echo "[+] Updating $y"
  curl -L -O "https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-${y}.json.gz"
done

gzip -t *.json.gz
rm -f nvd_offline_index.pkl
```

بعد از حذف Cache، اجرای بعدی ابزار Index جدید می‌سازد.

---

## اجرای کاملاً آفلاین

بعد از آماده‌سازی این دو بخش:

```text
دیتابیس cpe_search
فایل‌های NVD JSON
```

اجرای ابزار دیگر نیاز به اینترنت ندارد.

نمونه اجرای آفلاین:

```bash
python3 package_to_cve_offline.py \
  -i packages_ubuntu.txt \
  -o report.xlsx \
  --feeds ./nvd-feeds
```

در این حالت:

```text
NVD API Key نیاز نیست
اتصال اینترنت نیاز نیست
درخواستی به services.nvd.nist.gov ارسال نمی‌شود
```

---

## سناریوی پیشنهادی برای محیط‌های عملیاتی

روی سرور هدف فقط لیست پکیج گرفته شود:

```bash
dpkg-query -W -f='${binary:Package} ${Version}\n' > packages_ubuntu.txt
```

یا:

```bash
rpm -qa --queryformat '%{NAME} %{VERSION}-%{RELEASE}\n' > packages_rpm.txt
```

سپس فایل TXT به سیستم تحلیل‌گر منتقل شود.

روی سیستم تحلیل‌گر:

```bash
python3 package_to_cve_offline.py \
  -i packages_ubuntu.txt \
  -o customer_server_report.xlsx \
  --feeds ./nvd-feeds
```

فایل خروجی Excel برای بررسی اولیه، فیلتر Severity و تحلیل دستی استفاده شود.

---

## نکات مربوط به WSL

اگر ابزار داخل WSL اجرا شود، بهتر است پروژه داخل مسیر کاربر باشد، نه `/root`.

مسیر پیشنهادی:

```bash
mkdir -p ~/nvd-offline-package-audit
cd ~/nvd-offline-package-audit
```

برای باز کردن مسیر WSL از ویندوز:

```text
\\wsl.localhost\Ubuntu\home\<user>\nvd-offline-package-audit
```

اگر پروژه داخل `/root` ساخته شده باشد، ممکن است ویندوز در دسترسی به فایل‌ها خطای Permission بدهد.

---

## خطاهای رایج

### خطای NO_CPE_FOUND زیاد است

دلایل احتمالی:

```text
نام پکیج با نام محصول در CPE متفاوت است
نسخه پکیج شامل release-specific suffix است
پکیج مربوط به خود توزیع است و CPE عمومی ندارد
دیتابیس cpe_search قدیمی است
```

راهکار:

```text
دیتابیس CPE را به‌روزرسانی کنید
نام پکیج‌های مهم را دستی بررسی کنید
برای موارد حساس، CPE را دستی validate کنید
```

---

### اجرای اول کند است

طبیعی است.

در اجرای اول، ابزار فایل‌های NVD را می‌خواند و Cache محلی می‌سازد:

```text
nvd-feeds/nvd_offline_index.pkl
```

اجراهای بعدی سریع‌تر خواهند بود.

---

### خروجی CVE زیاد است

علت ممکن است یکی از موارد زیر باشد:

```text
تطبیق CPE دقیق نیست
CPE عمومی انتخاب شده است
نسخه Vendor patch شده ولی upstream version تغییر نکرده است
Backport patch در توزیع انجام شده است
```

راهکار:

```text
ستون Match Type را بررسی کنید
موارد CANDIDATE و PARTIAL را جداگانه بررسی کنید
خروجی را با advisory رسمی Vendor مقایسه کنید
```

---

## پیشنهاد برای تحلیل خروجی

در Excel ابتدا روی این ستون‌ها فیلتر بگذارید:

```text
Severity
Match Type
Package
CVE
```

اولویت بررسی:

```text
CRITICAL + EXACT/RANGE
HIGH + EXACT/RANGE
CRITICAL + CANDIDATE
HIGH + CANDIDATE
MEDIUM
LOW
```

برای گزارش رسمی، CVEهایی که فقط `CANDIDATE` هستند باید قبل از اعلام نهایی اعتبارسنجی شوند.

---

## Disclaimer

این ابزار فقط برای کمک به ممیزی امنیتی و تحلیل آفلاین پکیج‌ها طراحی شده است.

خروجی ابزار، آسیب‌پذیر بودن قطعی سیستم را اثبات نمی‌کند.

نتیجه نهایی باید با بررسی دستی، منابع رسمی Vendor و شرایط واقعی سیستم اعتبارسنجی شود.

این ابزار جایگزین اسکنرهای امنیتی، OVAL/RHSA/USN یا تحلیل تخصصی آسیب‌پذیری نیست.

---

## اجرای حداقلی

```bash
python3 package_to_cve_offline.py -i packages_ubuntu.txt -o report.xlsx --feeds ./nvd-feeds
```

بعد از آماده‌سازی دیتابیس‌ها، این دستور به‌صورت آفلاین اجرا می‌شود.
