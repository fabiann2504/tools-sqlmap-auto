# Recon Pipeline — Project fabz

> Automated recon & target discovery pipeline.
> **Credit: fabz**

---

## 📌 Apa Ini?

Tool all-in-one buat jalanin pipeline recon 3 tahap:

| Stage | Nama | Fungsi | Butuh |
|-------|------|--------|-------|
| 1 | **Scan Targets** | Ambil URL ber-param dari search engine (Bing, Yahoo, DDG) berdasarkan dork | `requests`, `beautifulsoup4`, `curl_cffi` |
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
    sudo apt update && sudo apt install -y sqlmap

**Linux / VPS / RDP (RHEL/CentOS/Fedora)**
    sudo dnf install -y sqlmap
    # atau
    sudo yum install -y sqlmap

**macOS (laptop)**
    brew install sqlmap

**Windows (laptop/RDP)**
    # 1. Install Python: https://www.python.org/downloads/
    # 2. Install sqlmap via pip
    pip install sqlmap

    # 3. Pastikan folder Scripts Python masuk PATH
    #    Biasanya: C:\Users\<nama>\AppData\Local\Programs\Python\Python3xx\Scripts

**Termux (HP Android)**
    pkg update && pkg install -y python git
    git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git ~/sqlmap
    echo 'alias sqlmap="python ~/sqlmap/sqlmap.py"' >> ~/.bashrc
    source ~/.bashrc

**Manual (semua platform)**
    git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git
    # Jalanin pake:
    python sqlmap/sqlmap.py -u "http://target/?id=1"

### Cek sqlmap udah keinstall
    sqlmap --version

Kalo muncul versi, berarti siap.

### sqlmap di path custom?
Jalanin tool pake flag:
    python sqli_tool.py --sqlmap-path /path/ke/sqlmap.py

---

## 📁 Struktur Folder

    sqli-tool/
    ├── sqli_tool.py          # main script (CLI + Flask)
    ├── split_dorks.py        # split & clean dork mentah (opsional)
    ├── requirements.txt      # dependency Python
    ├── README.md             # file ini
    ├── files/
    │   ├── dorks.txt         # file dork siap pakai (1 per baris)
    │   └── useragents.txt    # daftar user-agent (1 per baris)
    ├── templates/
    │   └── index.html        # UI web (Flask)
    ├── static/
    │   └── style.css         # styling UI web
    └── hasil/                # (AUTO) Tempat semua output
        ├── urls_crawl.txt    # Hasil crawl URL
        ├── urls_vuln.txt     # Hasil URL yang rentan
        └── sqlmap_dump/      # Hasil dump sqlmap

---

## 🚀 Instalasi

    # 1. Copy project
    cd sqli-tool

    # 2. Install dependency Python
    pip install -r requirements.txt

    # 3. Pastikan sqlmap udah ada
    sqlmap --version

    # 4. Siap jalan

---

## 🖥️ Cara Jalanin

### Mode Web (Flask) — Rekomendasi
    python sqli_tool.py --web

Buka browser: `http://127.0.0.1:5000`

Di UI ada 4 tombol:
- **Scan Targets** — Stage 1 (Ambil 30 dork random, crawl pake Bing/Yahoo/DDG)
- **Validate Findings** — Stage 2 (Cek SQLi pake payload `'`)
- **Process Queue** — Stage 3 (Tembak SQLmap)
- **Run Full Pipeline** — Stage 1 → 3 otomatis

Plus tombol:
- **Hapus Hasil** — Bersihin folder `hasil/`
- **Lihat Crawl / Vuln / Dump** — Liat isi file output

### Mode CLI — Langsung via Flag
    # Full pipeline
    python sqli_tool.py --mode full

    # Cuma Stage 1 (Scan)
    python sqli_tool.py --mode dork

    # Cuma Stage 2 (Validate)
    python sqli_tool.py --mode check

    # Cuma Stage 3 (SQLmap)
    python sqli_tool.py --mode sqlmap

---

## 🧠 Fitur Utama (Update Terbaru)

1. **Multi-Engine Scraper**: Gak cuma Bing, tapi juga nembak Yahoo dan DuckDuckGo. Kalo satu engine nge-blok, otomatis pindah ke engine lain.
2. **Anti-Hang (30 Random Dorks)**: Tiap kali Scan Targets, tool cuma ngambil **30 dork acak** dari `dorks.txt`. Ini biar laptop gak nge-hang dan hasilnya lebih variatif.
3. **Auto-Save ke `/hasil`**: Semua output (URL crawl, URL vuln, dump sqlmap) otomatis masuk ke folder `hasil/`. Gak bakal berserakan lagi.
4. **Anti-Duplikat**: Folder `hasil/` gak bakal ke-commit ke Git (kalo lo pake `.gitignore`).
5. **Tanpa Library Berat**: Gak pake Selenium, YOLO, atau `undetected-chromedriver`. Cuma pake `curl_cffi` yang ringan.

---

## 📤 Output

| File / Folder | Isi |
|---------------|-----|
| `hasil/urls_crawl.txt` | Hasil Stage 1 — URL ber-param dari dork |
| `hasil/urls_vuln.txt` | Hasil Stage 2 — URL yang confirmed error-based |
| `hasil/sqlmap_dump/` | Hasil Stage 3 — dump sqlmap per target (1 folder per URL) |

---

## ⚙️ Konfigurasi

### `files/dorks.txt`
Satu dork per baris. Baris diawali `#` = komentar.

    site:co.id inurl:"product.php?id="
    site:co.id inurl:"index.php?page="
    inurl:"product.php?id=" intext:"You have an error in your SQL syntax"

### `files/useragents.txt`
Satu user-agent per baris.

    Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...
    Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ...

### Flag `sqli_tool.py`
| Flag | Default | Fungsi |
|------|---------|--------|
| `--mode` | (menu) | `full` / `dork` / `check` / `sqlmap` |
| `--web` | off | Jalanin mode Flask |
| `--host` | `127.0.0.1` | Host Flask |
| `--port` | `5000` | Port Flask |
| `--technique` | `E` | Teknik sqlmap (`E`=error, `B`=boolean, `U`=union, `T`=time) |
| `--dbms` | `mysql` | DBMS target |
| `--sqlmap-path` | `sqlmap` | Path custom ke sqlmap |

---

## 🛠️ Troubleshooting

**`Hasil dorking 0 URL terus`**
→ IP lo mungkin lagi di-rate-limit sama search engine. Coba ganti jaringan (Tethering HP) atau tunggu beberapa jam.

**`sqlmap gak ketemu`**
→ Install sqlmap (lihat section di atas) atau pake `--sqlmap-path`.

**`Bing kosong, fallback DDG...`**
→ Wajar, Bing kadang kena anti-bot. Fallback ke Yahoo/DDG otomatis.

**`Stage 1 lama banget`**
→ Wajar, karena ada jeda 5 detik per dork biar gak di-ban. Tool cuma ngambil 30 dork random, jadi paling lama nunggu 2-3 menit.

**`ModuleNotFoundError`**
→ Jalanin `pip install -r requirements.txt` lagi.

---

## ⚠️ Disclaimer

Tool ini dibuat buat **pembelajaran, lab, dan target yang lo punya izin eksplisit**. Pake ke target orang tanpa izin itu **ilegal** dan di luar tanggung jawab author. Gunakan dengan bijak.

---

## 👤 Credit

**fabz** — author & maintainer

---

## 📜 Lisensi

MIT License — bebas dipake, dimodif, dan dibagiin, asal credit **fabz** tetep dicantumin.
