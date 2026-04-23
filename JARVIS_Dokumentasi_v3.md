# ⚡ JARVIS — Dokumentasi Lengkap v3.0
**Proyek:** Dangerous Human  
**File utama:** `telegram_agent.py`  
**Model AI:** `llama3.2:1b` via Ollama (lokal, offline)  
**Tanggal update:** 09 Maret 2026

---

## 🏗️ Arsitektur

```
Pesan Masuk (Telegram)
        │
        ▼
┌───────────────────┐
│  Protokol Keamanan│  ← Cek kata berbahaya → minta verifikasi 3 soal
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│   Hard Filter     │  ← Deteksi intent TANPA LLM (cepat & akurat)
└────────┬──────────┘
         │ Cocok?
    ┌────┴────┐
   Ya         Tidak
    │          │
    ▼          ▼
 Eksekusi    LLM Fallback
  Tool       (ChatOllama)
    │          │
    └────┬─────┘
         ▼
   Balas ke Telegram
```

> **Keunggulan v3.0:** Tools dieksekusi langsung oleh Python — tidak lewat LLM. Kompatibel dengan model kecil apapun, tidak ada output JSON acak.

---

## 🛠️ Semua Tools

### 1. Buka Aplikasi
```
buka chrome / buka notepad / buka spotify / buka roblox
open vscode / jalankan calculator
```
Aplikasi yang dikenal: chrome, firefox, edge, brave, spotify, vlc, notepad, vscode, word, excel, powerpoint, explorer, calc, paint, cmd, powershell, taskmgr, discord, telegram, whatsapp, steam, roblox, epic games

---

### 2. Tutup Aplikasi
```
tutup brave / close discord / kill chrome
```

---

### 3. YouTube
```
putar shape of you
play baby by justin bieber
cari musik lofi / dengerin jazz
```
Bot fetch HTML YouTube → ekstrak video ID pertama → buka langsung di browser.

---

### 4. Buka Website
```
buka github / buka arduino / buka coingecko
open dexscreener / buka chatgpt / buka tradingview
```
**80+ website tersedia:**

| Kategori | Contoh |
|---|---|
| AI & Search | chatgpt, gemini, claude, huggingface, perplexity |
| Social Media | youtube, instagram, twitter, reddit, tiktok |
| Dev Tools | github, stackoverflow, pypi, docker, w3schools, leetcode |
| Hardware/IoT | arduino, raspberry pi, hackaday, adafruit, ieee |
| Crypto/Trading | binance, tradingview, coingecko, dexscreener, dextools, forex |
| Berita | kompas, detik, cnbc, tempo, tribun, liputan6 |
| Productivity | gmail, gdrive, notion, zoom, slack, teams |
| E-commerce | tokopedia, shopee, lazada |

**Fallback cerdas:** tidak ada di database → langsung coba `https://www.{nama}.com`

---

### 5. Cari Barang E-commerce
```
cariin laptop
cari barang headset gaming
cari produk mechanical keyboard
cari laptop di shopee
```
Membuka **Tokopedia + Shopee + Lazada** sekaligus dengan query yang sama.

---

### 6. Kunci Layar
```
kunci layar / kunci laptop / lock screen / lock pc
```

---

### 7. Shutdown
```
matikan laptop / shutdown       ← perlu verifikasi keamanan
batal shutdown                  ← batalkan jika sudah terlanjur
```

---

### 8. Kalkulator
```
hitung 25 * 4 / kalkulasi 2 ** 10 / berapa hasil 100 / 3
```

---

### 9. Play/Pause Media
```
pause / jeda / play lagi / resume / lanjut musik
```
Menggunakan `pyautogui.press('playpause')` — kontrol media system-wide.

---

### 10. Terminal CMD
```
cmd: ipconfig
cmd: tasklist
terminal: dir C:\
```
> Perintah berbahaya (`hapus`, `delete`, `format`, dll) memicu verifikasi dulu.

---

### 11. Chat & Tanya Jawab
Semua pesan yang tidak cocok filter → ke LLM (llama3.2:1b) dengan conversation memory per-user.

---

## 🔐 Protokol Keamanan

Kata yang memicu verifikasi: `hapus`, `delete`, `format`, `rmdir`, `del`, `rm`, `drop`, `wipe`, `erase`, `rd /s`

User harus jawab **3 pertanyaan** dalam satu pesan:
1. Tempat & tanggal lahir
2. Nama kampus
3. Nama SMK

Jika salah → perintah **dibatalkan** otomatis.

---

## 📌 Perintah Telegram

| Perintah | Fungsi |
|---|---|
| `/start` | Tampilkan menu kemampuan |
| `/reset` | Hapus history & reset security state |
| `/status` | Cek model & waktu sistem |

---

## 🚀 Cara Menjalankan

```powershell
# Normal
python telegram_agent.py

# Stealth (tanpa jendela konsol)
# Klik dua kali: run_hidden.vbs

# Auto-Startup Windows
# Jalankan sebagai Admin: setup_startup.bat
```

---

## 📦 Dependensi

```bash
pip install pyTelegramBotAPI langchain-ollama pyautogui
ollama pull llama3.2:1b
```

---

## 🔮 Rekomendasi Future Update

### Prioritas Tinggi
- [ ] **Screenshot → Telegram** — `screenshot` → kirim gambar layar ke chat
- [ ] **Cek Status PC** — `status pc` → CPU, RAM, disk, IP address
- [ ] **Volume Control** — `volume 50 / naik volume / mute` via pycaw
- [ ] **Price Alert Crypto** — `alert btc 80000` → notif otomatis jika harga tembus threshold
- [ ] **Memory Permanen (SQLite)** — History tidak hilang saat bot restart

### Prioritas Menengah
- [ ] **Scrape Berita/Crypto** — `berita crypto hari ini` → ringkasan dari CoinDesk/CNBC
- [ ] **Reminder & Timer** — `ingatkan 30 menit lagi` → notif Telegram setelah countdown
- [ ] **Spotify API Control** — Pause/play/skip via Spotipy (lebih andal dari pyautogui)
- [ ] **Multi-User Whitelist** — Hanya chat_id tertentu yang bisa beri perintah OS
- [ ] **Keyboard Shortcut** — `tekan ctrl+c`, `tekan alt+f4` via pyautogui

### Prioritas Rendah / Long-term
- [ ] **Voice Note → Perintah** — Transcribe voice note pakai Whisper, proses sebagai teks
- [ ] **Kamera Snapshot** — `foto kamera` → ambil gambar webcam, kirim ke Telegram
- [ ] **Download YouTube** — `download [judul]` → yt-dlp untuk MP3/MP4
- [ ] **Real-time Crypto Price** — Harga langsung dari CoinGecko API tanpa buka browser
- [ ] **Upgrade Model** — Swap ke qwen2.5:7b atau mistral saat hardware lebih kuat

---

## 📁 Struktur File

```
C:\Projek iseng\
├── telegram_agent.py          ← Bot utama (v3.0) ✅ AKTIF
├── telegram_agent_ultra.py    ← Arsip: versi LangGraph agent
├── jarvis_fast_filter.py      ← Arsip: versi hard-filter only
├── run_hidden.vbs             ← Stealth mode (tanpa jendela)
├── setup_startup.bat          ← Auto-startup Windows
└── jarvis_memory.db           ← SQLite memory (arsip versi lama)
```
