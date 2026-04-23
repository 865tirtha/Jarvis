"""
=============================================================
  telegram_agent.py  —  JARVIS
  Proyek   : Dangerous Human
  Versi    : 3.0 (Hard-Filter + OS Tools + LLM Fallback)
  Deskripsi: Telegram Bot dengan kemampuan kontrol OS.
             Tools dieksekusi langsung (bukan via LLM),
             sehingga kompatibel dengan model kecil apapun.
=============================================================

Dependensi:
    pip install pyTelegramBotAPI langchain-ollama pyautogui

Cara menjalankan:
    python telegram_agent.py
=============================================================
"""

import os
import sys
import re
import math
import time
import threading
import datetime
import subprocess
import webbrowser
import traceback
import urllib.parse
import urllib.request
import io

try:
    import psutil
    import pyautogui
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
except ImportError as e:
    print(f"⚠️ Modul eksternal belum lengkap: {e}")

# Fix encoding Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import telebot

# ============================================================
# KONFIGURASI
# ============================================================
TELEGRAM_TOKEN  = "8602266927:AAGG90PmI0697sy4tDRsRiKA0qrebe0Y3yQ"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "llama3.2:1b"
MAX_HISTORY     = 3   # Pasang pesan yang disimpan per-user (3 interaksi User-AI = max 6 pesan)

# ============================================================
# PROTOKOL KEAMANAN
# ============================================================
JAWABAN_VALID = {
    "ttl"   : "jakarta, 21 februari 2006",
    "kuliah": "politeknik industri atmi",
    "smk"   : "smk ananda mitra industri deltamas",
}
KATA_BAHAYA = [
    "hapus", "delete", "format", "rmdir", "del ", "rm ",
    "drop", "wipe", "erase", "shutil.rmtree", "rd /s",
]

# State keamanan per-user: { chat_id: {"mode": "normal"|"verifikasi", "pending": str} }
user_security_state: dict = {}

# ============================================================
# DATABASE APLIKASI
# ============================================================
PETA_APLIKASI = {
    # Browser
    "chrome"      : "chrome",
    "firefox"     : "firefox",
    "edge"        : "msedge",
    "brave"       : "brave",
    # Media
    "spotify"     : "spotify",
    "vlc"         : "vlc",
    # Produktivitas
    "notepad"     : "notepad",
    "vscode"      : "code",
    "word"        : "winword",
    "excel"       : "excel",
    "powerpoint"  : "powerpnt",
    # Sistem
    "explorer"    : "explorer",
    "calculator"  : "calc",
    "paint"       : "mspaint",
    "cmd"         : "cmd",
    "powershell"  : "powershell",
    "task manager": "taskmgr",
    # Hiburan
    "discord"     : "discord",
    "telegram"    : "telegram",
    "whatsapp"    : "whatsapp",
    # Game
    "steam"       : "steam",
    "roblox"      : os.path.expandvars(r"%LOCALAPPDATA%\Roblox\Versions\RobloxPlayerLauncher.exe"),
    "epic"        : r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
    "epic games"  : r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
}

# ============================================================
# DATABASE WEBSITE
# ============================================================
PETA_WEBSITE = {
    # ── Search & AI ──────────────────────────
    "google"        : "https://www.google.com",
    "chatgpt"       : "https://chat.openai.com",
    "openai"        : "https://openai.com",
    "gemini"        : "https://gemini.google.com",
    "claude"        : "https://claude.ai",
    "perplexity"    : "https://www.perplexity.ai",
    "huggingface"   : "https://huggingface.co",
    "ollama"        : "https://ollama.ai",

    # ── Social Media ─────────────────────────
    "youtube"       : "https://www.youtube.com",
    "instagram"     : "https://www.instagram.com",
    "twitter"       : "https://twitter.com",
    "x"             : "https://x.com",
    "facebook"      : "https://www.facebook.com",
    "tiktok"        : "https://www.tiktok.com",
    "linkedin"      : "https://www.linkedin.com",
    "reddit"        : "https://www.reddit.com",
    "github"        : "https://github.com",
    "stackoverflow" : "https://stackoverflow.com",

    # ── Berita ───────────────────────────────
    "kompas"        : "https://www.kompas.com",
    "detik"         : "https://www.detik.com",
    "cnn"           : "https://www.cnnindonesia.com",
    "cnbc"          : "https://www.cnbcindonesia.com",
    "tempo"         : "https://www.tempo.co",
    "tribun"        : "https://www.tribunnews.com",
    "liputan6"      : "https://www.liputan6.com",
    "tirto"         : "https://tirto.id",
    "idn times"     : "https://www.idntimes.com",
    "viva"          : "https://www.viva.co.id",
    "suara"         : "https://www.suara.com",

    # ── Hardware, IoT & Mechatronics ─────────
    "arduino"       : "https://www.arduino.cc",
    "raspberry pi"  : "https://www.raspberrypi.com",
    "raspi"         : "https://www.raspberrypi.com",
    "hackaday"      : "https://hackaday.com",
    "sparkfun"      : "https://www.sparkfun.com",
    "adafruit"      : "https://www.adafruit.com",
    "instructables" : "https://www.instructables.com",
    "ieee"          : "https://www.ieee.org",

    # ── Dev & AI Tools ───────────────────────
    "langchain"     : "https://www.langchain.com",
    "pypi"          : "https://pypi.org",
    "docker"        : "https://www.docker.com",
    "kubernetes"    : "https://kubernetes.io",
    "mongodb"       : "https://www.mongodb.com",
    "postgresql"    : "https://www.postgresql.org",
    "w3schools"     : "https://www.w3schools.com",
    "mdn"           : "https://developer.mozilla.org",
    "leetcode"      : "https://leetcode.com",
    "codepen"       : "https://codepen.io",

    # ── Trading & Crypto ─────────────────────
    "binance"       : "https://www.binance.com",
    "tradingview"   : "https://www.tradingview.com",
    "coingecko"     : "https://www.coingecko.com",
    "coinmarketcap" : "https://coinmarketcap.com",
    "dexscreener"   : "https://dexscreener.com",
    "dextools"      : "https://www.dextools.io",
    "investing"     : "https://www.investing.com",
    "forex factory" : "https://www.forexfactory.com",
    "forex"         : "https://www.forexfactory.com",

    # ── Media & Forum ────────────────────────
    "medium"        : "https://medium.com",
    "quora"         : "https://www.quora.com",
    "kaskus"        : "https://www.kaskus.co.id",
    "pinterest"     : "https://www.pinterest.com",
    "vimeo"         : "https://vimeo.com",
    "telegram web"  : "https://web.telegram.org",
    "tele web"      : "https://web.telegram.org",

    # ── Productivity & Komunikasi ────────────
    "gmail"         : "https://mail.google.com",
    "drive"         : "https://drive.google.com",
    "gdrive"        : "https://drive.google.com",
    "zoom"          : "https://zoom.us",
    "slack"         : "https://slack.com",
    "teams"         : "https://teams.microsoft.com",
    "dropbox"       : "https://www.dropbox.com",
    "notion"        : "https://www.notion.so",
    "trello"        : "https://trello.com",

    # ── E-commerce (hanya buka homepage) ─────
    "tokopedia"     : "https://www.tokopedia.com",
    "shopee"        : "https://shopee.co.id",
    "lazada"        : "https://www.lazada.co.id",
}

# ============================================================
# TOOLS — FUNGSI EKSEKUSI LANGSUNG
# ============================================================

def tool_buka_website(query: str) -> str:
    q = query.lower()
    for k in ["buka ", "open ", "pergi ke ", "ke ", "web ", "website ", "situs ",
              "tolong ", "dong", "coba ", "jarvis "]:
        q = q.replace(k, "")
    nama = q.strip()

    # Exact match dulu
    url = PETA_WEBSITE.get(nama)
    if url:
        webbrowser.open(url)
        return f"🌐 Membuka {nama.title()}: {url}"

    # Partial match
    for key, val in PETA_WEBSITE.items():
        if key in nama or nama in key:
            webbrowser.open(val)
            return f"🌐 Membuka {key.title()}: {val}"

    # Fallback cerdas: tebak URL langsung → www.{nama}.com
    clean_nama = nama.replace(" ", "")
    url_tebakan = f"https://www.{clean_nama}.com"
    webbrowser.open(url_tebakan)
    return f"🌐 Tidak ada di database, mencoba membuka {url_tebakan}..."


def tool_buka_aplikasi(query: str) -> str:
    q = query.lower()
    for k in ["tolong ", "dong", "coba ", "jarvis ", "buka ", "open ", "jalankan ", "tolong"]:
        q = q.replace(k, "")
    nama_app = q.strip()

    executable = PETA_APLIKASI.get(nama_app)
    if executable:
        try:
            if os.path.isabs(executable) or "\\" in executable:
                os.startfile(executable)
            else:
                subprocess.Popen(executable, shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"✅ Membuka {nama_app.title()}..."
        except Exception as e:
            return f"❌ Gagal membuka {nama_app}: {e}"
    else:
        # Coba langsung jalankan nama tersebut
        try:
            subprocess.Popen(nama_app, shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"✅ Mencoba membuka '{nama_app}'..."
        except Exception as e:
            return f"❌ Gagal membuka '{nama_app}': {e}"


def tool_tutup_aplikasi(query: str) -> str:
    q = query.lower()
    for k in ["tolong ", "dong", "coba ", "jarvis ", "tutup ", "close ",
              "matikan aplikasi ", "kill ", "tolong"]:
        q = q.replace(k, "")
    nama_app = q.strip()

    # Cari exe di peta, fallback ke nama.exe
    info = PETA_APLIKASI.get(nama_app)
    if isinstance(info, str) and not info.endswith(".exe"):
        exe_name = info + ".exe"
    elif isinstance(info, str):
        exe_name = os.path.basename(info)
    else:
        exe_name = nama_app + ".exe"

    try:
        subprocess.run(["taskkill", "/F", "/IM", exe_name],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"✅ Aplikasi {nama_app.title()} berhasil ditutup!"
    except Exception as e:
        return f"❌ Gagal menutup {nama_app}: {e}"


def tool_youtube(query: str) -> str:
    kata_hapus = ("putar", "play", "tonton", "dengerin",
                  "di youtube", "youtube", "cari musik", "cari video",
                  "buka youtube cari")
    q = query.lower()
    for k in kata_hapus:
        q = q.replace(k, "")
    q = q.strip()
    if not q:
        return "❌ Query pencarian YouTube kosong."

    try:
        query_encoded = urllib.parse.quote_plus(q)
        search_url = f"https://www.youtube.com/results?search_query={query_encoded}"

        # Coba ekstrak video ID pertama dari HTML
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode(errors='replace')

        video_ids = re.findall(r'watch\?v=(\S{11})', html)
        if video_ids:
            url = f"https://www.youtube.com/watch?v={video_ids[0]}"
            webbrowser.open(url)
            return f"✅ Memutar: {q}"
        else:
            webbrowser.open(search_url)
            return f"✅ Membuka hasil pencarian YouTube: {q}"
    except Exception as e:
        # Fallback: buka halaman pencarian langsung
        try:
            webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(q)}")
            return f"✅ Membuka YouTube untuk: {q}"
        except:
            return f"❌ Gagal membuka YouTube: {e}"


def tool_kunci_layar() -> str:
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return "🔒 Layar berhasil dikunci."
    except Exception as e:
        subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
        return f"🔒 Perintah kunci layar dikirim. ({e})"


def tool_shutdown() -> str:
    subprocess.run(["shutdown", "/s", "/t", "10"])
    return "⚠️ Laptop akan mati dalam 10 detik. Ketik 'batal shutdown' untuk membatalkan."


def tool_batal_shutdown() -> str:
    subprocess.run(["shutdown", "/a"])
    return "✅ Shutdown dibatalkan."


def tool_cari_barang(query: str) -> str:
    q = query.lower()
    for k in ["cari ", "cariin ", "cari barang ", "cari produk ", "search ",
              "di tokopedia", "di shopee", "di lazada", "di bukalapak",
              "tokopedia", "shopee", "lazada", "bukalapak", "blibli",
              "tolong ", "dong", "coba ", "jarvis "]:
        q = q.replace(k, "")
    item = q.strip()
    if not item:
        return "❌ Query pencarian barang kosong."

    item_encoded = urllib.parse.quote_plus(item)
    urls = [
        f"https://www.tokopedia.com/search?st=product&q={item_encoded}",
        f"https://shopee.co.id/search?keyword={item_encoded}",
        f"https://www.lazada.co.id/catalog/?q={item_encoded}",
    ]
    for url in urls:
        webbrowser.open_new_tab(url)
    return f"🛒 Membuka Tokopedia, Shopee & Lazada untuk: *{item}*"


def tool_matematika(expr: str) -> str:
    try:
        angka_expr = re.sub(r'[^0-9+\-*/().\s]', '', expr)
        hasil = eval(angka_expr, {"__builtins__": None}, {"math": math})
        return f"🔢 Hasil: {hasil}"
    except Exception as e:
        return f"❌ Tidak bisa menghitung: {e}"


def tool_pause_media() -> str:
    try:
        import pyautogui
        pyautogui.press('playpause')
        return "⏯️ Sinyal Play/Pause berhasil dikirim!"
    except Exception as e:
        return f"❌ Gagal kontrol media: {e}"


def tool_terminal(command: str) -> str:
    """Jalankan perintah CMD (hanya lolos protokol keamanan)."""
    cmd_lower = command.lower()
    for kata in KATA_BAHAYA:
        if kata in cmd_lower:
            return (f"🔒 AKSES DITOLAK. Perintah mengandung operasi destruktif "
                    f"dan memerlukan verifikasi keamanan.")
    try:
        hasil = subprocess.run(command, shell=True, capture_output=True,
                               text=True, timeout=30,
                               encoding='utf-8', errors='replace')
        output = hasil.stdout.strip() or hasil.stderr.strip() or "(Selesai tanpa output)"
        if len(output) > 2000:
            output = output[:2000] + "\n...(dipotong)"
        return f"📤 Output:\n```\n{output}\n```"
    except subprocess.TimeoutExpired:
        return "⏱️ Timeout: Perintah > 30 detik dihentikan."
    except Exception as e:
        return f"❌ Error eksekusi: {e}"


def tool_screenshot() -> tuple[str, io.BytesIO | None]:
    """Mengambil screenshot layar dan mengembalikan objek BytesIO (tanpa simpan ke disk)."""
    try:
        if 'pyautogui' not in sys.modules:
            return "❌ Modul 'pyautogui' belum diinstall.", None
        
        # Ambil screenshot
        screenshot = pyautogui.screenshot()
        
        # Simpan ke memori buffer
        img_buffer = io.BytesIO()
        screenshot.save(img_buffer, format="PNG")
        img_buffer.name = "screenshot_jarvis.png"
        img_buffer.seek(0)
        
        return "📸 Screenshot berhasil diambil!", img_buffer
    except Exception as e:
        return f"❌ Gagal mengambil screenshot: {e}", None


def tool_cek_pc() -> str:
    """Membaca status CPU, RAM, dan Disk menggunakan psutil."""
    try:
        if 'psutil' not in sys.modules:
            return "❌ Modul 'psutil' belum diinstall."
            
        # CPU
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # RAM
        ram_info = psutil.virtual_memory()
        ram_total = ram_info.total / (1024 ** 3)
        ram_used = ram_info.used / (1024 ** 3)
        ram_percent = ram_info.percent
        
        # Disk (Drive C:)
        disk_info = psutil.disk_usage('C:\\')
        disk_total = disk_info.total / (1024 ** 3)
        disk_free = disk_info.free / (1024 ** 3)
        disk_percent = disk_info.percent
        
        report = (
            "📊 **LAPORAN STATUS HARDWARE** 📊\n\n"
            f"⚡ **CPU Usage:** `{cpu_usage}%`\n"
            f"🧠 **RAM Usage:** `{ram_used:.1f} GB` / `{ram_total:.1f} GB` ({ram_percent}%)\n"
            f"💾 **Disk C: Free:** `{disk_free:.1f} GB` dari `{disk_total:.1f} GB` (Terpakai: {disk_percent}%)"
        )
        return report
    except Exception as e:
        return f"❌ Gagal membaca status PC: {e}"


def tool_set_volume(query: str) -> str:
    """Mengatur level master volume Windows (0-100) menggunakan pycaw."""
    try:
        if 'pycaw' not in sys.modules:
            return "❌ Modul 'pycaw' belum diinstall."
            
        # Ekstrak angka dari query (contoh: "volume 50")
        t = query.lower()
        if "mute" in t and "unmute" not in t:
            target_vol = 0
        elif "max" in t or "100" in t:
            target_vol = 100
        else:
            match = re.search(r'\d+', t)
            if match:
                target_vol = int(match.group())
            else:
                return "❌ Gagal mendeteksi angka volume. Gunakan 'volume 50'."
                
        # Batasi 0-100
        target_vol = max(0, min(100, target_vol))
        
        # API pycaw
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        # Convert scalar 0.0 - 1.0 (Bukan decibel map untuk simpelnya, tapi panggil scalar asli)
        scalar_vol = target_vol / 100.0
        volume.SetMasterVolumeLevelScalar(scalar_vol, None)
        
        if target_vol == 0:
            return "🔇 Master Volume di-Mute (0%)."
        else:
            return f"🔊 Master Volume diatur ke: {target_vol}%"
            
    except Exception as e:
        return f"❌ Gagal mengatur volume: {e}"


# ============================================================
# HARD FILTER — Deteksi intent SEBELUM LLM dipanggil
# ============================================================
SAPAAN = {
    "hi", "hello", "halo", "hai", "hey", "hei",
    "pagi", "siang", "malam", "oke", "ok", "okay",
    "thanks", "makasih", "sip", "mantap", "iya",
    "ya", "tidak", "nggak", "done", "siap"
}
KATA_TANYA = (
    "apa", "siapa", "kenapa", "mengapa", "bagaimana",
    "gimana", "berapa", "dimana", "kapan", "apakah"
)
# Hanya blokir kata TRANSAKSI — nama e-commerce tetap boleh dibuka sebagai website
LARANGAN_TRANSAKSI = (
    "tambah ke keranjang", "checkout", "bayar sekarang",
    "beli sekarang", "order sekarang"
)
# E-commerce yang bisa dibuka / dicari barangnya
ECOMMERCE = ("tokopedia", "shopee", "lazada", "bukalapak", "blibli")


def hard_filter(text: str) -> dict | None:
    """
    Deteksi intent dari teks user TANPA LLM.
    Return dict { "tool": ..., "arg": ... } jika cocok,
    atau None jika harus dilempar ke LLM.
    """
    t = text.lower().strip()
    words = set(t.split())

    # ── Sapaan singkat ─────────────────────────────────────────
    if t in SAPAAN or words.issubset(SAPAAN):
        return {"tool": "direct", "reply": "Halo! Ada yang bisa dibantu? 😊"}

    # ── Blokir transaksi langsung ──────────────────────────────
    if any(k in t for k in LARANGAN_TRANSAKSI):
        return {"tool": "direct",
                "reply": "Maaf bos, aku tidak bisa transaksi. Tapi bisa buka situsnya atau cariin barangnya!"}

    # ── Batal shutdown ─────────────────────────────────────────
    if "batal shutdown" in t or "cancel shutdown" in t:
        return {"tool": "batal_shutdown"}

    # ── Shutdown ───────────────────────────────────────────────
    if any(k in t for k in ("matikan laptop", "shutdown", "turn off laptop")):
        return {"tool": "shutdown"}

    # ── Kunci layar ────────────────────────────────────────────
    if any(k in t for k in ("kunci laptop", "lock laptop", "kunci layar", "lock screen", "lock pc")):
        return {"tool": "kunci"}

    # ── Screenshot ─────────────────────────────────────────────
    if any(k in t for k in ("screenshot", "ss layar", "tangkap layar", "ambil ss")):
        return {"tool": "screenshot"}

    # ── Status PC / Hardware ───────────────────────────────────
    if any(k in t for k in ("status pc", "cek pc", "cek laptop", "status laptop", "info sistem", "resource laptop")):
        return {"tool": "cek_pc"}

    # ── Volume Control ─────────────────────────────────────────
    if any(k in t for k in ("volume", "suara ", "mute", "unmute")) and not "youtube" in t and not "cari" in t:
        return {"tool": "volume", "arg": text}

    # ── Pause/play media ───────────────────────────────────────
    if any(k in t for k in ("pause", "jeda", "play lagi", "resume", "lanjut musik", "stop video")):
        return {"tool": "pause_media"}

    # ── Cari barang di e-commerce ──────────────────────────────
    kata_cari_barang = ("cari barang", "cariin", "cari produk")
    cari_ecommerce   = any(k in t for k in kata_cari_barang) or \
                       ("cari " in t and any(e in t for e in ECOMMERCE))
    if cari_ecommerce:
        return {"tool": "cari_barang", "arg": text}

    # ── YouTube ────────────────────────────────────────────────
    kata_yt = ("putar ", "play ", "tonton ", "dengerin ",
               "cari musik", "cari video", "buka youtube", "youtube")
    if any(k in t for k in kata_yt):
        return {"tool": "youtube", "arg": text}

    # ── Matematika ─────────────────────────────────────────────
    kata_math = ("hitung", "berapa hasil", "kalkulasi", "tambah", "kurang", "kali", "bagi")
    if any(k in t for k in kata_math) and re.search(r'\d', t):
        return {"tool": "matematika", "arg": text}

    # ── Tutup aplikasi ─────────────────────────────────────────
    if any(k in t for k in ("tutup ", "close ", "matikan aplikasi ", "kill ")):
        return {"tool": "tutup_app", "arg": text}

    # ── Buka aplikasi ──────────────────────────────────────────
    if any(k in t for k in ("buka ", "open ", "jalankan ")) and "youtube" not in t:
        # Cek website dulu sebelum aplikasi
        q_check = t
        for k in ["buka ", "open ", "jalankan "]:
            q_check = q_check.replace(k, "")
        q_check = q_check.strip()
        # Jika cocok dengan nama website atau multi-kata (ada spasi) → buka web
        if q_check in PETA_WEBSITE or any(k in q_check for k in PETA_WEBSITE):
            return {"tool": "buka_web", "arg": text}
        return {"tool": "buka_app", "arg": text}

    # ── Terminal / CMD ─────────────────────────────────────────
    if t.startswith(("cmd:", "terminal:", "run:", "jalankan cmd")):
        cmd = re.sub(r'^(cmd:|terminal:|run:|jalankan cmd)\s*', '', t).strip()
        return {"tool": "terminal", "arg": cmd}

    return None  # Lempar ke LLM


def eksekusi_filter(hasil: dict) -> str:
    tool = hasil.get("tool")
    arg  = hasil.get("arg", "")

    if tool == "direct":
        return hasil.get("reply", "")
    elif tool == "youtube":
        return tool_youtube(arg)
    elif tool == "matematika":
        return tool_matematika(arg)
    elif tool == "kunci":
        return tool_kunci_layar()
    elif tool == "shutdown":
        return tool_shutdown()
    elif tool == "batal_shutdown":
        return tool_batal_shutdown()
    elif tool == "buka_web":
        return tool_buka_website(arg)
    elif tool == "cari_barang":
        return tool_cari_barang(arg)
    elif tool == "buka_app":
        return tool_buka_aplikasi(arg)
    elif tool == "tutup_app":
        return tool_tutup_aplikasi(arg)
    elif tool == "pause_media":
        return tool_pause_media()
    elif tool == "cek_pc":
        return tool_cek_pc()
    elif tool == "volume":
        return tool_set_volume(arg)
    elif tool == "terminal":
        return tool_terminal(arg)
    elif tool == "screenshot":
        # Exception khusus untuk screenshot (akan ditangkap di layer atas main loop karena me-return tipe berbeda)
        return "Special:Screenshot"
    return "❌ Tool tidak dikenal."


# ============================================================
# PROTOKOL KEAMANAN — Verifikasi
# ============================================================
def mengandung_kata_bahaya(teks: str) -> bool:
    teks_lower = teks.lower()
    return any(kata in teks_lower for kata in KATA_BAHAYA)


def validasi_jawaban_keamanan(jawaban: str) -> tuple[bool, str]:
    baris = [b.strip() for b in jawaban.strip().splitlines() if b.strip()]
    if len(baris) < 3:
        return False, (
            "⚠️ Kirim 3 jawaban dalam 3 baris:\n"
            "Baris 1: Tempat tanggal lahir\n"
            "Baris 2: Nama kampus\n"
            "Baris 3: Nama SMK"
        )
    salah = []
    if baris[0].lower() != JAWABAN_VALID["ttl"]:
        salah.append("❌ Jawaban TTL salah")
    if baris[1].lower() != JAWABAN_VALID["kuliah"]:
        salah.append("❌ Jawaban Kuliah salah")
    if baris[2].lower() != JAWABAN_VALID["smk"]:
        salah.append("❌ Jawaban SMK salah")
    if salah:
        return False, "\n".join(salah)
    return True, "✅ Semua jawaban benar."


PESAN_VERIFIKASI = (
    "🔒 *MODE VERIFIKASI KEAMANAN AKTIF*\n\n"
    "Perintah Anda mengandung operasi destruktif.\n"
    "Jawab 3 pertanyaan berikut dalam *satu pesan* (pisahkan dengan baris baru):\n\n"
    "1️⃣ Tempat tanggal lahir Anda?\n"
    "2️⃣ Kuliah di mana?\n"
    "3️⃣ SMK di mana?"
)


# ============================================================
# LLM — ChatOllama langsung (fallback jika hard_filter miss)
# ============================================================
print("[Sistem] Menghubungkan ke Ollama ...")
try:
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.7,
        num_predict=512,
        num_ctx=2048,
    )
    print(f"[Sistem] Model '{OLLAMA_MODEL}' siap.")
except Exception:
    print(f"[ERROR] Gagal koneksi ke Ollama!\n{traceback.format_exc()}")
    sys.exit(1)

SYSTEM_PROMPT = (
    "Kamu adalah JARVIS, asisten AI pribadi yang cerdas dan ramah. "
    "Jawab dalam Bahasa Indonesia yang natural dan singkat (maksimal 3 kalimat). "
    "JANGAN keluarkan JSON, kode teknis, atau memanggil tool — cukup balas dengan teks biasa. "
    "Kamu memiliki memory dan bisa mengingat percakapan sebelumnya."
)

# Conversation history per-user: { chat_id: [HumanMessage, AIMessage, ...] }
user_histories: dict[int, list] = {}


def get_llm_reply(chat_id: int, teks_user: str) -> str:
    waktu = datetime.datetime.now().strftime("%A, %d-%m-%Y %H:%M:%S")
    hist  = user_histories.get(chat_id, [])

    messages = [SystemMessage(content=f"{SYSTEM_PROMPT}\nWaktu sekarang: {waktu}")]
    messages.extend(hist)
    messages.append(HumanMessage(content=teks_user))

    response = llm.invoke(messages)
    jawaban  = response.content.strip()

    # Simpan ke history
    if chat_id not in user_histories:
        user_histories[chat_id] = []
    user_histories[chat_id].append(HumanMessage(content=teks_user))
    user_histories[chat_id].append(AIMessage(content=jawaban))
    
    # Batasi panjang history secara ketat agar model 1B tidak berhalusinasi (max 6 pesan)
    if len(user_histories[chat_id]) > MAX_HISTORY * 2:
        user_histories[chat_id] = user_histories[chat_id][-(MAX_HISTORY * 2):]

    return jawaban


def reset_history(chat_id: int):
    user_histories.pop(chat_id, None)
    user_security_state.pop(chat_id, None)


# ============================================================
# INISIASI TELEGRAM BOT
# ============================================================
print("[Sistem] Menginisiasi Telegram Bot ...")
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)

# Hapus sesi lama untuk cegah error 409
try:
    bot.delete_webhook(drop_pending_updates=True)
    print("[Sistem] Sesi lama dibersihkan.")
except Exception as e:
    print(f"[PERINGATAN] Gagal hapus webhook: {e}")

print("[Sistem] Bot siap. Menunggu pesan...\n")


# ============================================================
# HANDLER /start
# ============================================================
@bot.message_handler(commands=['start', 'mulai'])
def handle_start(message):
    nama = message.from_user.first_name or "Pengguna"
    bot.reply_to(message,
        f"⚡ *JARVIS* — Dangerous Human Project\n\n"
        f"Halo, *{nama}*! Saya siap melayani.\n\n"
        "🛠️ *Yang bisa saya lakukan:*\n"
        "• `buka chrome` / `buka notepad` — Buka aplikasi\n"
        "• `tutup brave` — Tutup aplikasi\n"
        "• `putar shape of you` — YouTube\n"
        "• `kunci layar` — Kunci laptop\n"
        "• `matikan laptop` — Shutdown (10 detik)\n"
        "• `hitung 25 * 4` — Kalkulator\n"
        "• `pause` — Play/Pause media\n"
        "• `cmd: ipconfig` — Jalankan terminal\n\n"
        "📌 *Perintah:*\n"
        "/reset — Hapus memori\n"
        "/status — Cek status sistem",
        parse_mode="Markdown"
    )


# ============================================================
# HANDLER /status
# ============================================================
@bot.message_handler(commands=['status'])
def handle_status(message):
    waktu = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    bot.reply_to(message,
        f"📊 *Status JARVIS*\n\n"
        f"🤖 Model: `{OLLAMA_MODEL}`\n"
        f"💾 Memory: `In-RAM per-user`\n"
        f"⏰ Waktu: `{waktu}`",
        parse_mode="Markdown"
    )


# ============================================================
# HANDLER /reset
# ============================================================
@bot.message_handler(commands=['reset', 'lupa'])
def handle_reset(message):
    reset_history(message.chat.id)
    bot.reply_to(message, "🔄 Memori percakapan dan status keamanan direset!")


# ============================================================
# MODE HIBERNASI (HEMAT RESOURCE)
# ============================================================
last_active_time = time.time()
is_sleeping = False

def cek_status_tidur():
    global last_active_time, is_sleeping
    while True:
        waktu_sekarang = time.time()
        # cek kalo nganggur lebih dari 10 detik
        if waktu_sekarang - last_active_time > 10 and not is_sleeping:
            print("🌱 10 detik nganggur. bot masuk mode hibernasi (hemat RAM & bumi)")
            is_sleeping = True
            # Di sini bisa disisipkan logika hapus memori / unload Llama
            
        time.sleep(1) # cek status tiap 1 detik aja biar ga berat


# ============================================================
# HANDLER PESAN TEKS — INTI BOT
# ============================================================
@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_semua_pesan(message):
    chat_id   = message.chat.id
    teks_user = message.text.strip()
    nama_user = message.from_user.username or message.from_user.first_name or str(chat_id)

    print(f"[Pesan] @{nama_user} ({chat_id}): {teks_user}")
    bot.send_chat_action(chat_id, 'typing')

    # Bangunkan bot dari Hibernasi
    global last_active_time, is_sleeping
    if is_sleeping:
        print("🚀 bangun woi! ada request masuk! (to the moon!)")
        is_sleeping = False
    last_active_time = time.time()

    state = user_security_state.get(chat_id, {"mode": "normal"})

    # ══ CABANG A: Sedang dalam mode verifikasi ══════════════════
    if state.get("mode") == "verifikasi":
        lulus, feedback = validasi_jawaban_keamanan(teks_user)
        if lulus:
            perintah_tertunda = state.get("pending", "")
            user_security_state.pop(chat_id, None)
            bot.reply_to(message,
                f"✅ *Identitas terverifikasi!*\nMenjalankan: `{perintah_tertunda}`",
                parse_mode="Markdown"
            )
            try:
                hasil = subprocess.run(perintah_tertunda, shell=True,
                                       capture_output=True, text=True,
                                       timeout=30, encoding='utf-8', errors='replace')
                output = hasil.stdout.strip() or hasil.stderr.strip() or "(Selesai tanpa output)"
                if len(output) > 3000:
                    output = output[:3000] + "\n...(dipotong)"
                bot.send_message(chat_id, f"📤 Output:\n```\n{output}\n```",
                                 parse_mode="Markdown")
            except Exception as e:
                bot.send_message(chat_id, f"❌ Error: {e}")
        else:
            user_security_state.pop(chat_id, None)
            bot.reply_to(message,
                f"🚫 *Verifikasi Gagal!*\n{feedback}\n\nPerintah dibatalkan.",
                parse_mode="Markdown"
            )
        return

    # ══ CABANG B: Cek kata bahaya → masuk verifikasi ════════════
    if mengandung_kata_bahaya(teks_user):
        user_security_state[chat_id] = {"mode": "verifikasi", "pending": teks_user}
        bot.reply_to(message, PESAN_VERIFIKASI, parse_mode="Markdown")
        print(f"[SECURITY] @{nama_user} masuk mode verifikasi.")
        return

    # ══ CABANG C: Hard Filter → eksekusi tool langsung ══════════
    hasil_filter = hard_filter(teks_user)
    if hasil_filter:
        jawaban = eksekusi_filter(hasil_filter)
        
        # Penanganan Khusus Tipe Data Non-String (cth: Screenshot)
        if jawaban == "Special:Screenshot":
            msg_text, img_buffer = tool_screenshot()
            if img_buffer:
                bot.send_photo(chat_id, img_buffer, caption=msg_text)
                print(f"[TOOL] screenshot → Sukses dikirim")
            else:
                bot.send_message(chat_id, msg_text)
                print(f"[TOOL] screenshot → Gagal: {msg_text}")
            return # Selesai, tidak perlu kirim teks lagi
            
        print(f"[TOOL] {hasil_filter.get('tool')} → {jawaban[:80]}")
    else:
        # ══ CABANG D: Lempar ke LLM untuk jawaban teks ══════════
        try:
            jawaban = get_llm_reply(chat_id, teks_user)
        except Exception:
            detail = traceback.format_exc()
            print(f"[ERROR LLM]\n{detail}")
            jawaban = (
                "⚠️ Maaf, Ollama sedang tidak dapat dijangkau. "
                "Pastikan Ollama aktif dan coba lagi."
            )

    print(f"[JARVIS] → {jawaban[:100]}{'...' if len(jawaban) > 100 else ''}\n")

    # Kirim balasan
    try:
        bot.reply_to(message, jawaban)
    except Exception:
        try:
            for i in range(0, len(jawaban), 4000):
                bot.send_message(chat_id, jawaban[i:i+4000])
        except Exception as e2:
            bot.send_message(chat_id, f"⚠️ Gagal mengirim: {e2}")


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  JARVIS — Dangerous Human Project v3.0")
    print(f"  Model   : {OLLAMA_MODEL}")
    print("  Filter  : Hard-Filter + LLM Fallback")
    print("  Tools   : YouTube, Buka/Tutup App, Kunci, Shutdown,")
    print("            Web, E-commerce, Matematika, Media Control,")
    print("            Terminal CMD, Screenshot, Cek PC, Volume")
    print("  Status  : AKTIF — Tekan Ctrl+C untuk berhenti")
    print("=" * 60 + "\n")

    # Jalankan monitor hibernasi di background thread
    threading.Thread(target=cek_status_tidur, daemon=True).start()

    while True:
        try:
            print("[JARVIS] Polling dimulai ...")
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=60,
                skip_pending=True,
                allowed_updates=["message"],
            )
        except KeyboardInterrupt:
            print("\n[JARVIS] Sistem dimatikan. Over and out.")
            break
        except Exception:
            print(f"[ERROR] Polling crash, restart dalam 5 detik...\n{traceback.format_exc()}")
            time.sleep(5)
