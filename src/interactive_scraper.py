#!/usr/bin/env python3
"""Interactive scraper: meminta input user dan mengekspor CSV/XLSX

Jalankan:
  python src/interactive_scraper.py

Saat dijalankan, skrip akan menanyakan:
- Pekerjaan (occupation)
- Point (boleh dikosongkan)
- Nominated state (boleh dikosongkan)

Hasil: file CSV dan Excel di folder kerja saat ini.
"""
from __future__ import annotations

import datetime
import logging
import os
import sys

from typing import Optional

import pandas as pd


# Import helper functions from scraper.py (same folder)
try:
    from scraper import fetch_page, parse_tables, combine_tables, build_params
except Exception:
    # If run in a different working dir, try adding script dir to path
    script_dir = os.path.dirname(__file__)
    sys.path.insert(0, script_dir)
    from scraper import fetch_page, parse_tables, combine_tables, build_params


def prompt_input(prompt: str) -> Optional[str]:
    val = input(prompt).strip()
    return val if val != "" else None


def make_out_paths(occupation: Optional[str], point: Optional[str], state: Optional[str]) -> tuple[str, str]:
    t = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    occ = occupation or "any"
    pt = point or "any"
    st = state or "any"
    base = f"eoi_{occ}_{pt}_{st}_{t}"
    return base + ".csv", base + ".xlsx"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print("Masukkan parameter untuk scraping SkillSelect EOI (tekan Enter untuk melewatkan yang opsional)")
    occupation = prompt_input("Pekerjaan (occupation code/name): ")
    point = prompt_input("Point (mis. 75): ")
    nominated_state = prompt_input("Nominated state (mis. VIC): ")

    params = build_params(occupation, point, nominated_state)
    logging.info("Mengirim permintaan dengan parameter: %s", params)
    html = fetch_page(params)

    dfs = parse_tables(html)
    csv_path, xlsx_path = make_out_paths(occupation, point, nominated_state)

    if not dfs:
        logging.warning("Tidak ditemukan tabel pada halaman. Menyimpan HTML dan membuat CSV fallback.")
        html_path = csv_path.replace('.csv', '.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        fallback_df = pd.DataFrame({
            'html_saved_to': [html_path],
            'note': ['No HTML tables found; saved raw HTML for inspection'],
            'occupation': [occupation],
            'point': [point],
            'nominated_state': [nominated_state]
        })
        fallback_df.to_csv(csv_path, index=False)
        fallback_df.to_excel(xlsx_path, index=False)
        logging.info("Saved fallback CSV: %s and XLSX: %s", csv_path, xlsx_path)
        return

    combined = combine_tables(dfs)
    # Tambahkan kolom parameter sumber
    combined['occupation'] = occupation
    combined['point'] = point
    combined['nominated_state'] = nominated_state

    # Simpan CSV dan Excel
    combined.to_csv(csv_path, index=False)
    try:
        combined.to_excel(xlsx_path, index=False)
    except Exception as e:
        logging.warning("Gagal menyimpan Excel (%s). Pastikan openpyxl/xlrd tersedia. Error: %s", xlsx_path, e)

    logging.info("Selesai. Disimpan: %s (CSV) dan %s (XLSX)", csv_path, xlsx_path)


if __name__ == '__main__':
    main()
