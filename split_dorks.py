#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Split & clean dork mentah jadi kategori rapi + batch.
Credit: fabz
"""

import os
import re
import sys
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(BASE_DIR, "files")
RAW_FILE = os.path.join(FILES_DIR, "raw_dorks.txt")
OUT_DIR = FILES_DIR
BATCH_SIZE = 50

CATEGORIES = {
    "sqli.txt": [
        r"inurl:.*\?id=", r"inurl:.*\?page=", r"inurl:.*\?cat=",
        r"inurl:.*\?pid=", r"inurl:.*\?cid=", r"inurl:.*\?prod",
        r"inurl:.*\?book", r"inurl:.*\?item", r"inurl:.*\?news",
        r"inurl:.*\?article", r"inurl:.*\?product", r"inurl:.*\?view",
        r"inurl:.*\?detail", r"inurl:.*\?show", r"inurl:.*\?download",
        r"inurl:.*\?file", r"inurl:.*\?include", r"inurl:.*\?lang",
        r"inurl:.*\?menu", r"inurl:.*\?pg=", r"inurl:.*\?p=",
        r"inurl:.*\?t=", r"inurl:.*\?topic", r"inurl:.*\?thread",
        r"inurl:.*\?board", r"inurl:.*\?no=", r"inurl:.*\?num=",
        r"inurl:.*\?code=", r"inurl:.*\?action=", r"inurl:.*\?op=",
        r"inurl:.*\?mod=", r"inurl:.*\?do=", r"inurl:.*\?go=",
        r"inurl:.*\?load=", r"inurl:.*\?read=", r"inurl:.*\?search=",
        r"inurl:.*\?q=", r"inurl:.*\?s=",
    ],
    "error_sqli.txt": [
        r"You have an error in your SQL syntax",
        r"Warning:\s*mysql_fetch", r"Warning:\s*mysql_query",
        r"Supplied argument is not a valid MySQL",
        r"Unclosed quotation mark", r"XPATH syntax error",
        r"SQLSTATE\[", r"ORA-\d{5}",
        r"Microsoft OLE DB Provider for SQL Server",
        r"PostgreSQL.*ERROR", r"syntax error at or near",
        r"Incorrect syntax near",
    ],
    "lfi.txt": [
        r"\?include=", r"\?incl=", r"\?inc=", r"\?file=",
        r"\?page=", r"\?path=", r"\?dir=", r"\?load=",
        r"\?read=", r"\?root=", r"\?config=", r"\?base_dir=",
        r"\?basepath=", r"\?phpbb_root_path=", r"\?sourcedir=",
        r"\?GALLERY_BASEDIR=",
    ],
    "index_of.txt": [
        r'"index of /"', r'"index of/"', r'intitle:"index of"',
        r'"parent directory"',
    ],
    "password_file.txt": [
        r'passwd', r'htpasswd', r'\.pwd', r'\.passwd',
        r'password\.txt', r'config\.php', r'\.env', r'\.sql',
        r'\.mdb', r'\.bak',
    ],
}

def is_valid_dork(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return False
    if len(line) < 10:
        return False
    if re.fullmatch(r"[?&][a-zA-Z0-9_]+=", line):
        return False
    if re.fullmatch(r"[\W_]+", line):
        return False
    if not any(c in line for c in ["=", ":", "/", '"', "ext:", "intitle:", "inurl:", "intext:", "site:", "filetype:"]):
        return False
    return True

def load_raw(path):
    if not os.path.exists(path):
        print(f"[!] File mentah gak ada: {path}")
        print(f"    Simpen file dork lo sebagai: {path}")
        sys.exit(1)
    with open(path, encoding="utf-8", errors="ignore") as f:
        return [ln.strip() for ln in f]

def classify(line):
    matched = []
    for cat, patterns in CATEGORIES.items():
        for pat in patterns:
            if re.search(pat, line, re.IGNORECASE):
                matched.append(cat)
                break
    return matched

def write_file(path, header, items):
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + "\n\n")
        for d in items:
            f.write(d + "\n")

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    lines = load_raw(RAW_FILE)
    print(f"[*] Total baris mentah: {len(lines)}")

    seen = set()
    valid = []
    skipped = 0
    for ln in lines:
        if not is_valid_dork(ln):
            skipped += 1
            continue
        key = ln.lower()
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        valid.append(ln)

    print(f"[*] Baris valid & unik: {len(valid)}")
    print(f"[*] Baris di-skip (invalid/duplikat): {skipped}")

    buckets = {cat: [] for cat in CATEGORIES}
    uncategorized = []
    for ln in valid:
        cats = classify(ln)
        if not cats:
            uncategorized.append(ln)
        for c in cats:
            buckets[c].append(ln)

    for cat, items in buckets.items():
        path = os.path.join(OUT_DIR, cat)
        header = f"# Kategori: {cat}\n# Total: {len(items)} dork\n# Credit: fabz"
        write_file(path, header, items)
        print(f"[+] {cat}: {len(items)} dork")

    path = os.path.join(OUT_DIR, "uncategorized.txt")
    write_file(path, f"# Uncategorized: {len(uncategorized)} dork\n# Credit: fabz", uncategorized)
    print(f"[+] uncategorized.txt: {len(uncategorized)} dork")

    sqli_all = []
    for cat in ["sqli.txt", "error_sqli.txt"]:
        sqli_all.extend(buckets[cat])
    sqli_all = list(dict.fromkeys(sqli_all))
    path = os.path.join(OUT_DIR, "dorks.txt")
    header = f"# Dork siap pakai buat Recon Pipeline\n# Total: {len(sqli_all)} dork\n# Credit: fabz"
    write_file(path, header, sqli_all)
    print(f"[+] dorks.txt (siap pakai): {len(sqli_all)} dork")

    # Batch splitting
    total_batch = math.ceil(len(sqli_all) / BATCH_SIZE) if sqli_all else 0
    for i in range(total_batch):
        chunk = sqli_all[i * BATCH_SIZE:(i + 1) * BATCH_SIZE]
        bpath = os.path.join(OUT_DIR, f"dorks_batch_{i+1:02d}.txt")
        header = f"# Batch {i+1}/{total_batch} — {len(chunk)} dork\n# Credit: fabz"
        write_file(bpath, header, chunk)
    if total_batch:
        print(f"[+] {total_batch} file batch dibuat (dorks_batch_XX.txt, {BATCH_SIZE} dork/file)")

    print("\n[+] Selesai. Cek folder:", OUT_DIR)

if __name__ == "__main__":
    main()