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
👉 `data/eoi_ss/eoi_[Parameter]_[Timestamp].csv`

**Catatan Log:** Proses ekspor akan dicatat otomatis di `data/log/eoi_ss/eoi_ss.log`.

## Menjalankan Ekspor NERO Data (Nowcast of Employment)

Skrip baru untuk mengunduh dataset ketenagakerjaan dari Jobs and Skills Australia (JSA) secara otomatis. Skrip ini secara khusus dirancang menggunakan `curl_cffi` untuk menghindari pemblokiran Cloudflare/Incapsula pada situs web pemerintah.

**Cara Menggunakan:**

```bash
python tools/nero_employment_data_au.py
```

**Fitur NERO Tool:**

- Mengunduh rilis `Main NERO Data` & `Regional and Northern Australia Data` terbaru.
- Ekstraksi `.zip` otomatis langsung ke format CSV.
- **Konversi otomatis ke Excel (.xlsx)**: Mengingat ukuran data NERO yang sangat besar (>3,9 juta baris), skrip akan otomatis memecah output Excel per **State** (NSW, VIC, dsb) dan melakukan **chunking** (perpenggalan) jika data satu negara bagian masih melebihi limit 1 juta baris Excel.
- File keluaran disimpan ke `data/nero/`.
- File catatan histori log akan disimpan ke `data/log/nero/nero.log`.

## Menjalankan Ekspor Kuota Tahunan Migration (State & National)

Skrip baru untuk menarik kuota imigrasi (Migration Program Planning Levels & State Nomination Allocations) langsung dari website resmi Home Affairs. Skrip ini secara khusus mem-_bypass_ pemblokiran dari Akamai dan mengekstrak tabel HTML yang disembunyikan di dalam field JSON.

**Cara Menggunakan:**

```bash
python tools/migration_quotas_au.py
```

**Fitur Quotas Tool:**

- Mengunduh data "National Migration Program Planning Levels".
- Mengunduh data "State and territory nomination allocations".
- Menyimpan hasil ekstraksi secara otomatis ke format **Excel (.xlsx)** dan CSV di dalam folder `data/migration_quota/`.
- File catatan histori log akan disimpan ke `data/log/migration_quota/migration_quotas.log`.

## Menjalankan Ekspor Status Visa State (Program Status)

Skrip baru untuk memantau status pembukaan program nominasi negara bagian (State Nomination) dan tipe visa yang tersedia (190, 491, dll) langsung dari portal resmi masing-masing AI (Investment NSW, Live in Melbourne, dsb).

**Cara Menggunakan:**

```bash
python tools/state_visa_types_au.py
```

**Fitur Visa Status Tool:**

- Memantau 8 portal migrasi State/Territory Australia secara otomatis.
- Deteksi status program (**Open**, **Active**, **Closed**, atau **Paused**) berdasarkan analisis kata kunci.
- Menyimpan hasil ringkasan ke format **Excel (.xlsx)** dan CSV di `data/visa_types/`.
- File catatan histori log akan disimpan ke `data/log/visa_types/state_visa_scraper.log`.

---

## Struktur Folder Proyek Baru

Untuk menjaga repositori tetap bersih dan rapi, disarankan mengikuti struktur folder berikut:

- `tools/`  
  Berisi _tools_ andalan proyek ini:
  - `eoi_skillselect_au.py` (Tool ekspor Qlik/EOI utama)
  - `nero_employment_data_au.py` (Tool automasi NERO data)
  - `migration_quotas_au.py` (Tool scraper Kuota Imigrasi)
  - `state_visa_types_au.py` (Tool pemantau Status Visa State)
- `src/`  
  Berisi skrip _scraper_ dari iterasi / percobaan program versi terdahulu.
- `data/`  
  Berisi semua input statis dan direktori output sistem otomatis:
  - `data/eoi_ss/` : Folder keluaran hasil ekspor dari dashboard Qlik/EOI
  - `data/nero/` : Folder keluaran hasil download & ekstrak NERO ZIP Data (CSV & Split Excel)
  - `data/migration_quota/` : Folder keluaran Migration Quotas (Excel & CSV)
  - `data/visa_types/` : Folder keluaran Status Visa State (Excel & CSV)
  - `data/log/` : Menampung seluruh riwayat log pemakaian dari skrip tools terkait
- `tests/`  
  Kumpulan arsip skrip percobaan backend (seperti `qix_test_*.py`) yang digunakan saat me-_reverse-engineer_ dan menjebol limitasi dimensi Qlik Engine.

---

*Catatan Tambahan: Jika Anda ke depannya ingin menjalankan *scraping* ini secara *multi-thread* otomatis setiap bulan (`batch requests`), Anda cukup mengimpor fungsi `qix_export()` di dalam file integrasi Anda sendiri.*
