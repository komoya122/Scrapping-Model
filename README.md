# SkillSelect EOI Data Extractor

Ringkasan: Proyek ini berisi kumpulan skrip untuk menarik data Expression of Interest (EOI) SkillSelect dari dashboard Qlik Sense (Imigrasi Australia). Skrip utama saat ini menggunakan **Qlik Engine API (WebSockets)** untuk melakukan _bypass_ penuh pada frontend website, sehingga penarikan data 10x lebih cepat, anti-gagal (100% reliable bebas _timeout_ browser), dan mampu mengekspor kombinasi lebih dari 2 parameter sekaligus dalam satu tabel!

## Persyaratan

Pastikan Anda sudah menginstal dependensi Python yang dibutuhkan:

```bash
pip install -r requirements.txt
```

## Menjalankan Ekspor Data (Tool Utama)

Skrip paling stabil dan tercepat untuk mengambil file CSV (termasuk Occupation, Points, Status, Nominated State, dll.) berada di:  
`tools/eoi_skillselect_au.py`

**Cara Menggunakan:**

```bash
python tools/eoi_skillselect_au.py
```

Program akan berjalan diam-diam (_headless background_) dan meminta Anda mengisi parameter interaktif di terminal:

1. **Occupation**: Ketik kode (mis. `261111`) atau nama (mis. `Data Analyst`). Tekan Enter untuk mengosongkan.
2. **Point**: Ketik batas poin (mis. `75`). Tekan Enter untuk mengosongkan.
3. **Nominated State**: Ketik state (mis. `VIC`, `NSW`). Tekan Enter untuk mengosongkan.
4. **Visa Type**: Pilih dari daftar angka yang disediakan (189, 190, 491).
5. **As At Month**: Pilih bulan yang tersedia untuk ditarik datanya, atau biarkan kosong (All) untuk mengunduh semua historis bulan yang digabungkan secara otomatis.

💡 **Fitur Otomatis**: Skrip ini menggunakan API WebSocket untuk mem-bypass UI website. Anda dapat menarik dan menggabungkan data semua bulan sekaligus! Qlik Server dipaksa memproses dataset raksasa (sampai jutaan data kombinasi) tanpa membatasi jumlah kolom parameter!

**Hasil Data:**
Skrip akan mencetak progresnya dan langsung mengunduh file hasil ke dalam:
👉 `data/output/eoi_[Parameter]_[Timestamp].csv`

## Menjalankan Ekspor NERO Data (Nowcast of Employment)

Skrip baru untuk mengunduh dataset ketenagakerjaan dari Jobs and Skills Australia (JSA) secara otomatis. Skrip ini secara khusus dirancang menggunakan `curl_cffi` untuk menghindari pemblokiran Cloudflare/Incapsula pada situs web pemerintah.

**Cara Menggunakan:**

```bash
python tools/nero_employment_data_au.py
```

**Fitur NERO Tool:**

- Mengunduh rilis `Main NERO Data` & `Regional and Northern Australia Data` terbaru.
- Ekstraksi `.zip` otomatis langsung ke format CSV.
- File keluaran disimpan ke `data/nero/`.

---

## Struktur Folder Proyek Baru

Untuk menjaga repositori tetap bersih dan rapi, disarankan mengikuti struktur folder berikut:

- `tools/`  
  Berisi _tools_ andalan proyek ini:
  - `eoi_skillselect_au.py` (Tool ekspor Qlik/EOI utama)
  - `nero_employment_data_au.py` (Tool automasi NERO data)
- `src/`  
  Berisi skrip _scraper_ dari iterasi / percobaan program versi terdahulu.
- `data/`  
  Berisi semua input statis dan output sistem.
  - `data/output/` : **SANGAT PENTING**. Di sinilah seluruh data `.csv` final, serta _dump files_ JSON atau _screenshot errors_ akan secara otomatis tersimpan setiap kali skrip dijalankan.
- `tests/`  
  Kumpulan arsip skrip percobaan backend (seperti `qix_test_*.py`) yang digunakan saat me-_reverse-engineer_ dan menjebol limitasi dimensi Qlik Engine.

---

*Catatan Tambahan: Jika Anda ke depannya ingin menjalankan *scraping* ini secara *multi-thread* otomatis setiap bulan (`batch requests`), Anda cukup mengimpor fungsi `qix_export()` di dalam file integrasi Anda sendiri.*
