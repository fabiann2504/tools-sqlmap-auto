# Recon Pipeline — Project fabz

> Automated recon & target discovery pipeline.
> **Credit: fabz**

---

## 📌 Apa Ini?

Tool all-in-one buat jalanin pipeline recon 3 tahap:

| Stage | Nama | Fungsi | Butuh |
|-------|------|--------|-------|
| 1 | **Scan Targets** | Ambil URL ber-param dari search engine berdasarkan dork | `requests`, `beautifulsoup4` |
| 2 | **Validate Findings** | Probe error-based buat filter target yang beneran vulnerable | `requests` |
| 3 | **Process Queue** | Auto-feed target tervalidasi ke sqlmap | **sqlmap (WAJIB)** |

Tool ini bisa jalan dalam **2 mode**:
- **CLI** — menu interaktif atau flag `--mode`
- **Web (Flask)** — dashboard di browser, kontrol pipeline lewat tombol

---

## ⚠️ WAJIB: sqlmap Harus Terinstall

Stage 3 **gak bakal jalan** kalo sqlmap gak kedetek. Tool bakal ngecek otomatis pas start dan kasih instruksi install kalo gak ada.

### Install sqlmap per Platform

**Linux / VPS / RDP (Debian/Ubuntu)**
```bash
sudo apt update && sudo apt install -y sqlmap
Linux / VPS / RDP (RHEL/CentOS/Fedora)

bash
sudo dnf install -y sqlmap
# atau
sudo yum install -y sqlmap
macOS (laptop)

bash
brew install sqlmap
Windows (laptop/RDP)

powershell
# 1. Install Python: https://www.python.org/downloads/
# 2. Install sqlmap via pip
pip install sqlmap

# 3. Pastikan folder Scripts Python masuk PATH
#    Biasanya: C:\Users\<nama>\AppData\Local\Programs\Python\Python3xx\Scripts
Termux (HP Android)

bash
pkg update && pkg install -y python git
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git ~/sqlmap
echo 'alias sqlmap="python ~/sqlmap/sqlmap.py"' >> ~/.bashrc
source ~/.bashrc
Manual (semua platform)

bash
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git
# Jalanin pake:
python sqlmap/sqlmap.py -u "http://target/?id=1"
Cek sqlmap udah keinstall
bash
sqlmap --version
Kalo muncul versi, berarti siap.

sqlmap di path custom?
Jalanin tool pake flag:

bash
python sqli_tool.py --sqlmap-path /path/ke/sqlmap.py
📁 Struktur Folder
text
sqli-tool/
├── sqli_tool.py          # main script (CLI + Flask)
├── split_dorks.py        # split & clean dork mentah
├── requirements.txt      # dependency Python
├── README.md             # file ini
├── files/
│   ├── raw_dorks.txt     # (input) file dork mentah lo
│   ├── dorks.txt         # (auto) hasil split, siap pakai
│   ├── sqli.txt          # (auto) dork SQLi parameter-based
│   ├── error_sqli.txt    # (auto) dork error message SQLi
│   ├── lfi.txt           # (auto) dork LFI/RFI
│   ├── index_of.txt      # (auto) dork index of
│   ├── password_file.txt # (auto) dork file sensitif
│   ├── uncategorized.txt # (auto) sisanya
│   ├── dorks_batch_*.txt # (auto) batch 50 dork
│   └── useragents.txt    # daftar user-agent (1 per baris)
├── templates/
│   └── index.html        # UI web (Flask)
└── static/
    └── style.css         # styling UI web
🚀 Instalasi
bash
# 1. Copy project
cd sqli-tool

# 2. Install dependency Python
pip install -r requirements.txt

# 3. Pastikan sqlmap udah ada
sqlmap --version

# 4. Siap jalan
🧹 Split & Clean Dork (Pertama Kali)
Kalo lo punya file dork mentah (misal newsnews.phpid=.txt), jalanin dulu:

bash
# 1. Copy file mentah lo
cp newsnews.phpid=.txt files/raw_dorks.txt

# 2. Split & clean
python split_dorks.py
Hasilnya di files/:

dorks.txt — siap pakai (gabungan SQLi + error SQLi, dedup)

dorks_batch_01.txt, dorks_batch_02.txt, dst — batch 50 dork

sqli.txt, error_sqli.txt, lfi.txt, index_of.txt, password_file.txt, uncategorized.txt

Tips: Buat test awal, pake batch kecil dulu:

bash
mv files/dorks.txt files/dorks_full.txt
cp files/dorks_batch_01.txt files/dorks.txt
🖥️ Cara Jalanin
Mode CLI — Menu Interaktif
bash
python sqli_tool.py
Muncul menu:

text
1. Full pipeline (Stage 1 -> 2 -> 3)
2. Stage 1 - Scan Targets
3. Stage 2 - Validate Findings
4. Stage 3 - Process Queue (butuh sqlmap)
5. Cek status sqlmap
6. Keluar
Mode CLI — Langsung via Flag
bash
# Full pipeline
python sqli_tool.py --mode full

# Cuma Stage 1
python sqli_tool.py --mode dork

# Cuma Stage 2
python sqli_tool.py --mode check

# Cuma Stage 3
python sqli_tool.py --mode sqlmap

# Custom teknik & DBMS
python sqli_tool.py --mode sqlmap --technique BEU --dbms mysql

# sqlmap di path custom
python sqli_tool.py --sqlmap-path /opt/sqlmap/sqlmap.py
Mode Web (Flask)
bash
python sqli_tool.py --web
# atau custom host/port (akses dari LAN)
python sqli_tool.py --web --host 0.0.0.0 --port 8080
Buka browser: http://127.0.0.1:5000

Di UI ada 4 tombol:

Scan Targets — Stage 1

Validate Findings — Stage 2

Process Queue — Stage 3 (butuh sqlmap)

Run Full Pipeline — Stage 1 → 3 otomatis

Plus endpoint /health buat cek status sqlmap:

bash
curl http://127.0.0.1:5000/health
Response:

json
{
  "sqlmap_found": true,
  "sqlmap_path": "/usr/bin/sqlmap",
  "sqlmap_version": "1.8.4#stable"
}
📤 Output
File / Folder	Isi
raw_urls.txt	Hasil Stage 1 — URL ber-param dari dork
vuln_urls.txt	Hasil Stage 2 — URL yang confirmed error-based
sqlmap_output/	Hasil Stage 3 — dump sqlmap per target (1 folder per URL)
⚙️ Konfigurasi
files/dorks.txt
Satu dork per baris. Baris diawali # = komentar.

text
site:co.id inurl:"product.php?id="
site:co.id inurl:"index.php?page="
inurl:"product.php?id=" intext:"You have an error in your SQL syntax"
files/useragents.txt
Satu user-agent per baris.

text
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ...
Flag sqli_tool.py
Flag	Default	Fungsi
--mode	(menu)	full / dork / check / sqlmap
--web	off	Jalanin mode Flask
--host	127.0.0.1	Host Flask
--port	5000	Port Flask
--technique	E	Teknik sqlmap (E=error, B=boolean, U=union, T=time)
--dbms	mysql	DBMS target
--sqlmap-path	sqlmap	Path custom ke sqlmap
--skip-sqlmap-check	off	Skip validasi sqlmap (gak disaranin)
🧪 Teknik sqlmap yang Didukung
Flag	Teknik	Kapan dipake
E	Error-based	Default, paling cepet kalo target ngasih error
B	Boolean-based blind	Kalo gak ada error tapi response beda true/false
U	Union-based	Kalo jumlah kolom bisa ditebak
T	Time-based blind	Kalo gak ada output sama sekali
BEU	Kombinasi	Biar sqlmap auto-detect
Contoh:

bash
python sqli_tool.py --mode sqlmap --technique BEU
🛠️ Troubleshooting
sqlmap gak ketemu
→ Install sqlmap (lihat section di atas) atau pake --sqlmap-path.

Bing kosong, fallback DDG...
→ Wajar, Bing kadang kena anti-bot. Fallback ke DuckDuckGo otomatis.

Hasil dorking dikit
→ Tambahin dork di files/dorks.txt, atau pake Google Custom Search API buat hasil lebih stabil.

Stage 1 lama banget
→ Terlalu banyak dork. Pake batch: cp files/dorks_batch_01.txt files/dorks.txt. Atau tambahin delay di run_scraper().

ModuleNotFoundError: No module named 'flask'
→ pip install flask

ModuleNotFoundError: No module named 'requests'
→ pip install -r requirements.txt

sqlmap stuck / lambat
→ Turunin --level / --risk / --threads di sqli_tool.py bagian run_sqlmap().

⚠️ Disclaimer
Tool ini dibuat buat pembelajaran, lab, dan target yang lo punya izin eksplisit. Pake ke target orang tanpa izin itu ilegal dan di luar tanggung jawab author. Gunakan dengan bijak.

👤 Credit
fabz — author & maintainer