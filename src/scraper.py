#!/usr/bin/env python3
"""Scraper untuk SkillSelect EOI data (ANZSCO Skill Select)

Script ini mengambil halaman HTML dari endpoint publik yang diberikan dan
mengekstrak semua tabel menjadi satu CSV untuk analisis lebih lanjut.

Usage:
  python src/scraper.py --occupation 261111 --point 75 --nominated-state VIC -o output.csv

Catatan:
 - Endpoint bisa mengembalikan beberapa tabel; semua tabel akan digabungkan
   menjadi satu DataFrame (outer join pada kolom berbeda) dan diekspor ke CSV.
"""
from __future__ import annotations

import argparse
import logging
from typing import Dict, List

import pandas as pd
import requests
from bs4 import BeautifulSoup


URL_BASE = (
    "https://api.dynamic.reports.employment.gov.au/anonap/extensions/"
    "hSKLS02_SkillSelect_EOI_Data/hSKLS02_SkillSelect_EOI_Data.html"
)


def fetch_page(params: Dict[str, str]) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; skill-scraper/1.0; +https://github.com)"
    }
    resp = requests.get(URL_BASE, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_tables(html: str) -> List[pd.DataFrame]:
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    dfs: List[pd.DataFrame] = []
    for idx, table in enumerate(tables):
        # Extract headers
        header_row = table.find("tr")
        headers = []
        if header_row:
            for th in header_row.find_all(["th", "td"]):
                headers.append(th.get_text(strip=True))

        rows = []
        for tr in table.find_all("tr")[1:]:
            cols = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if not any(cols):
                continue
            rows.append(cols)

        if not headers and rows:
            # fallback: generate column names
            max_cols = max(len(r) for r in rows)
            headers = [f"col_{i}" for i in range(max_cols)]

        if rows:
            df = pd.DataFrame(rows)
            if len(headers) == df.shape[1]:
                df.columns = headers
            else:
                # try to align by padding
                if df.shape[1] < len(headers):
                    # fewer columns than headers: pad rows
                    for _ in range(len(headers) - df.shape[1]):
                        df[f"_pad_{_}"] = ""
                df.columns = headers[: df.shape[1]]
            df["_source_table_idx"] = idx
            dfs.append(df)

    return dfs


def combine_tables(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    if not dfs:
        return pd.DataFrame()
    # Use outer concat to preserve all columns from different tables
    combined = pd.concat(dfs, axis=0, ignore_index=True, sort=False)
    return combined


def build_params(occupation: str | None, point: str | None, nominated_state: str | None) -> Dict[str, str]:
    params: Dict[str, str] = {}
    if occupation:
        params["occupation"] = occupation
    if point:
        params["point"] = point
    if nominated_state:
        # endpoint might expect nominatedState or nominated_state; include both
        params["nominatedState"] = nominated_state
        params["nominated_state"] = nominated_state
    return params


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape SkillSelect EOI data and save CSV")
    parser.add_argument("--occupation", help="Occupation code or name (e.g. 261111)")
    parser.add_argument("--point", help="Points value filter (e.g. 75)")
    parser.add_argument("--nominated-state", help="Nominated state (e.g. VIC)")
    parser.add_argument("-o", "--output", default="eoi_data.csv", help="Output CSV path")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.info("Building request parameters")
    params = build_params(args.occupation, args.point, args.nominated_state)
    logging.info("Requesting page from endpoint")
    html = fetch_page(params)

    logging.info("Parsing tables from page")
    dfs = parse_tables(html)
    if not dfs:
        logging.warning("No tables found on page; saving raw HTML and CSV fallback")
        # Save a small HTML file for manual inspection
        html_path = args.output.replace('.csv', '.html')
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        # Create a small CSV indicating where the raw HTML was saved so caller
        # always receives a CSV file as output.
        fallback_df = pd.DataFrame({
            "html_saved_to": [html_path],
            "note": ["No HTML tables found; saved raw HTML for inspection"]
        })
        fallback_df.to_csv(args.output, index=False)
        logging.info("Saved fallback CSV pointing to %s", html_path)
        return

    logging.info("Combining %d tables", len(dfs))
    combined = combine_tables(dfs)
    logging.info("Saving CSV to %s", args.output)
    combined.to_csv(args.output, index=False)
    logging.info("Saved %d rows and %d columns", combined.shape[0], combined.shape[1])


if __name__ == "__main__":
    main()
