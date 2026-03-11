# 1Panel WAF & Logs Viewer

Sebuah aplikasi *viewer* berbasis Python Flask yang ringan dan interaktif untuk membaca log serangan WAF dan log traffic website langsung dari database SQLite bawaan **1Panel OpenResty WAF**.

Aplikasi ini membaca data langsung dari direktori produksi 1Panel WAF secara *real-time* tanpa perlu menyalin atau menduplikasi database. Dilengkapi dengan antarmuka berbasis Bootstrap 5 dan DataTables untuk pencarian, pengurutan, dan paginasi yang cepat, bahkan untuk puluhan ribu baris log.

## Fitur

*   **Dashboard Ringkasan:** Menampilkan total permintaan, serangan, dan log yang diblokir.
*   **WAF Attack Logs Viewer:** Melihat detail serangan yang diblokir oleh WAF, lengkap dengan IP, *Rule Match*, dan tindakan yang diambil.
*   **Site Traffic Logs Viewer:** Melihat log *traffic* spesifik per website (HTTP Status, URI, Response Time, dll) yang tersedia di 1Panel.
*   **Real-time Database Access:** Membaca database bawaan `/opt/1panel/apps/openresty/openresty/1pwaf/data/db` secara langsung jika dijalankan di server produksi.

## Persyaratan Sistem

*   Python 3.8+
*   Akses *root* (atau permission membaca direktori WAF 1Panel) jika dijalankan di server produksi.

## Instalasi (Lokal / Development)

1. Clone repositori ini atau salin semua file ke dalam satu folder.
2. Buat Virtual Environment (opsional tapi disarankan):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependensi (termasuk Flask dan Gunicorn):
   ```bash
   pip install -r requirements.txt
   ```
4. Jalankan aplikasi Flask:
   ```bash
   python3 app.py
   ```
5. Buka di browser: `http://127.0.0.1:5000`

> **Catatan:** Jika dijalankan di lokal, aplikasi akan mencari file database di folder `db` yang berada di direktori yang sama dengan `app.py`.

## Tutorial Deployment ke Server Produksi (Menggunakan Gunicorn & Systemd)

Untuk menjalankan aplikasi ini secara *real-time* di server produksi (tempat 1Panel Anda berada), ikuti langkah-langkah berikut:

### 1. Persiapkan Aplikasi

Salin folder aplikasi ini ke server produksi Anda (misal ke direktori `/opt/1pwaf-viewer`).

```bash
cd /opt
sudo git clone <url_repo_anda> 1pwaf-viewer  # Atau gunakan scp/ftp untuk mengunggah file
cd 1pwaf-viewer
```

### 2. Install Dependensi

Sangat disarankan menggunakan virtual environment agar tidak mengganggu sistem Python bawaan OS.

```bash
sudo apt update && sudo apt install python3-venv python3-pip -y  # Untuk Ubuntu/Debian
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt
```

### 3. Konfigurasi Systemd Service

Agar aplikasi berjalan di latar belakang dan otomatis *restart* saat server *reboot*, kita buat *service file* untuk `systemd`.

Buat file baru:
```bash
sudo nano /etc/systemd/system/1pwaf-viewer.service
```

Isi dengan konfigurasi berikut (sesuaikan *path* jika Anda menempatkannya di direktori lain):

```ini
[Unit]
Description=Gunicorn instance to serve 1Panel WAF Viewer
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/opt/1pwaf-viewer
Environment="PATH=/opt/1pwaf-viewer/venv/bin"
# Binding ke port 5000 (sesuaikan jika port ini sudah terpakai)
ExecStart=/opt/1pwaf-viewer/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

*Catatan: Kita menggunakan user `root` agar aplikasi memiliki izin (permission) untuk membaca database SQLite milik OpenResty WAF di direktori `/opt/1panel/apps/...`. Jika tidak menggunakan root, pastikan user yang Anda set memiliki hak akses baca (read) ke direktori database WAF.*

### 4. Mulai Service

Aktifkan dan jalankan service yang baru saja dibuat:

```bash
sudo systemctl daemon-reload
sudo systemctl start 1pwaf-viewer
sudo systemctl enable 1pwaf-viewer
```

Cek status service untuk memastikan aplikasi berjalan tanpa error:

```bash
sudo systemctl status 1pwaf-viewer
```

### 5. Konfigurasi Reverse Proxy (Opsional tapi Disarankan)

Aplikasi sekarang berjalan di `http://IP_SERVER:5000`. Jika Anda ingin mengaksesnya menggunakan domain (misal: `waf.domainanda.com`) dan menggunakan HTTPS, Anda bisa mengatur Reverse Proxy langsung dari 1Panel:

1. Buka 1Panel Dashboard -> **Websites**.
2. Klik **Create Website** -> Pilih tab **Reverse Proxy**.
3. Masukkan domain Anda (contoh: `waf.domainanda.com`).
4. Di bagian **Proxy Target**, masukkan `http://127.0.0.1:5000`.
5. Simpan dan konfigurasikan SSL seperti biasa melalui menu 1Panel.

Sekarang Anda bisa mengakses 1Panel WAF Viewer secara aman melalui domain Anda!
