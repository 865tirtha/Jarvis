"""
=============================================================
  telegram_agent_ultra.py  —  JARVIS ULTRA
  Proyek   : Dangerous Human
  Versi    : 2.0  (OS-Level Autonomous Agent)
  Deskripsi: Telegram Bot penuh dengan kemampuan mengontrol
             OS, protokol keamanan militer, dan conversation
             memory permanen berbasis SQLite.
=============================================================

DEPENDENSI:
  pip install pyTelegramBotAPI langchain-ollama langgraph langgraph-checkpoint-sqlite

CARA MENJALANKAN (manual):
  python "c:\\Projek iseng\\telegram_agent_ultra.py"

AUTO-STARTUP (tersembunyi): lihat run_hidden.vbs & setup_startup.bat
=============================================================
"""

import os
import sys
import math
import datetime
import subprocess
import webbrowser
import traceback
import urllib.parse
import urllib.request
import re

# Fix encoding Windows agar karakter Unicode tidak error
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─────────────────────────────────────────────
# IMPORT LANGCHAIN / LANGGRAPH
# ─────────────────────────────────────────────
from langchain_ollama import ChatOllama
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent   # Menggunakan modul LangGraph
from langchain_core.messages import SystemMessage, trim_messages   # Untuk membungkus system prompt dan trimming pesan

# SQLite Checkpointer — memory PERMANEN (tidak hilang saat bot restart)
# Jika package belum ada: pip install langgraph-checkpoint-sqlite
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    SQLITE_TERSEDIA = True
except ImportError:
    from langgraph.checkpoint.memory import MemorySaver
    SQLITE_TERSEDIA = False
    print("[PERINGATAN] langgraph-checkpoint-sqlite tidak ditemukan. Menggunakan MemorySaver (RAM).")
    print("[PERINGATAN] Install dengan: pip install langgraph-checkpoint-sqlite\n")

import telebot

# ─────────────────────────────────────────────
# KONFIGURASI UTAMA
# ─────────────────────────────────────────────
TELEGRAM_TOKEN  = "8602266927:AAGG90PmI0697sy4tDRsRiKA0qrebe0Y3yQ"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "llama3.2:1b"
DB_PATH         = "c:\\Projek iseng\\jarvis_memory.db"   # Lokasi file SQLite memori

# ─────────────────────────────────────────────
# PROTOKOL KEAMANAN — Jawaban Verifikasi
# (case-insensitive, dibandingkan setelah .strip().lower())
# ─────────────────────────────────────────────
JAWABAN_VALID = {
    "ttl"   : "jakarta, 21 februari 2006",
    "kuliah": "politeknik industri atmi",
    "smk"   : "smk ananda mitra industri deltamas",
}

# Kata kunci yang memicu mode verifikasi keamanan
KATA_BAHAYA = [
    "hapus", "delete", "format", "rmdir", "del ", "rm ",
    "drop", "wipe", "erase", "shutil.rmtree", "rd /s",
]

# ─────────────────────────────────────────────
# STATE MESIN KEAMANAN PER-USER
# ─────────────────────────────────────────────
# Struktur: { chat_id: {"mode": "normal"|"verifikasi", "pending": str} }
user_security_state: dict = {}

# Peta thread_id per-user (untuk /reset memory)
user_thread_map: dict = {}


# =============================================================
# BAGIAN 1: TOOLS — ALAT BANTU AI (OS-LEVEL)
# =============================================================

# ── Peta nama aplikasi → executable (bisa diperluas) ──────────
PETA_APLIKASI = {
    # Browser
    "chrome"      : "chrome",
    "firefox"     : "firefox",
    "edge"        : "msedge",
    "brave"       : "brave",
    # Media
    "spotify"     : "spotify",
    "vlc"         : "vlc",
    "winamp"      : "winamp",
    # Produktivitas
    "notepad"     : "notepad",
    "notepad++"   : "notepad++",
    "vscode"      : "code",
    "word"        : "winword",
    "excel"       : "excel",
    "powerpoint"  : "powerpnt",
    "outlook"     : "outlook",
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
    "epic games"  : "epicgameslauncher",
}


@tool
def buka_aplikasi(nama_app: str) -> str:
    """Buka aplikasi Windows berdasarkan nama (misal: notepad, spotify, chrome)."""
    try:
        kunci = nama_app.strip().lower()
        # Cari di peta aplikasi
        executable = PETA_APLIKASI.get(kunci, kunci)  # fallback: langsung pakai nama aslinya

        subprocess.Popen(
            executable,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return f"✅ Berhasil membuka aplikasi: '{nama_app}'"
    except Exception as e:
        return f"❌ Gagal membuka '{nama_app}': {e}"


@tool
def cari_youtube(query: str) -> str:
    """Cari dan langsung putar video pertama di YouTube berdasarkan query."""
    try:
        query_encoded = urllib.parse.quote_plus(query)
        search_url = f"https://www.youtube.com/results?search_query={query_encoded}"
        
        # Ambil HTML hasil pencarian
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode()
        
        # Ekstrak ID video pertama menggunakan Regex
        video_ids = re.findall(r"watch\?v=(\S{11})", html)
        if video_ids:
            video_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
            webbrowser.open(video_url)
            return f"✅ Berhasil menemukan video. Sekarang memutar: {video_url}"
        else:
            # Fallback jika tidak ditemukan ID di HTML
            webbrowser.open(search_url)
            return f"❓ Tidak dapat mengekstrak video pertama secara otomatis. Membuka hasil pencarian: {search_url}"
    except Exception as e:
        return f"❌ Gagal memutar YouTube: {e}"


@tool
def cari_barang_belanja(item: str) -> str:
    """Hanya gunakan untuk mencari barang di e-commerce. DILARANG KERAS menggunakan tool ini jika pengguna memberikan perintah sistem operasi seperti mengunci layar/laptop, membuka aplikasi, atau mematikan PC."""
    try:
        q = urllib.parse.quote_plus(item)
        urls = [
            f"https://www.tokopedia.com/search?st=product&q={q}",
            f"https://shopee.co.id/search?keyword={q}",
            f"https://www.lazada.co.id/catalog/?q={q}",
        ]
        for url in urls:
            webbrowser.open_new_tab(url)
        return f"✅ Membuka Tokopedia, Shopee, dan Lazada untuk mencari: '{item}'"
    except Exception as e:
        return f"❌ Gagal membuka marketplace: {e}"


@tool
def jalankan_perintah_terminal(command: str) -> str:
    """Jalankan perintah CMD/Shell Windows (hanya perintah aman yang lolos protokol keamanan)."""
    # Periksa kata bahaya — tolak di level tool juga sebagai lapisan kedua keamanan
    perintah_lower = command.lower()
    for kata in KATA_BAHAYA:
        if kata in perintah_lower:
            return (
                f"🔒 AKSES DITOLAK oleh Protokol Keamanan JARVIS.\n"
                f"Perintah '{command}' mengandung operasi destruktif dan memerlukan verifikasi."
            )

    try:
        hasil = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',
            errors='replace',
        )
        output = hasil.stdout.strip() or hasil.stderr.strip() or "(Perintah selesai tanpa output)"
        # Batasi output agar tidak terlalu panjang
        if len(output) > 2000:
            output = output[:2000] + "\n...(output dipotong)"
        return f"✅ Output:\n```\n{output}\n```"
    except subprocess.TimeoutExpired:
        return "⏱️ Timeout: Perintah memakan waktu > 30 detik dan dihentikan."
    except Exception as e:
        return f"❌ Error saat eksekusi: {e}"


@tool
def hitung_matematika(ekspresi: str) -> str:
    """Hitung ekspresi matematika Python (misal: '25 * 4' atau 'math.sqrt(144)')."""
    try:
        hasil = eval(ekspresi, {"__builtins__": None}, {"math": math})
        return str(hasil)
    except Exception as e:
        return f"❌ Error saat menghitung '{ekspresi}': {e}"


@tool
def cek_waktu_sekarang(query: str = "") -> str:
    """Kembalikan waktu, tanggal, dan hari saat ini secara akurat."""
    sekarang = datetime.datetime.now()
    return sekarang.strftime("%A, %d-%m-%Y pukul %H:%M:%S WIB")


@tool
def kunci_layar_laptop() -> str:
    """PENTING: Gunakan tool ini HANYA JIKA pengguna secara eksplisit meminta untuk mengunci laptop, lock pc, atau mengamankan layar dari jarak jauh. Mengeksekusi OS LockWorkStation."""
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return "🔒 Layar berhasil dikunci. Protokol keamanan aktif."
    except Exception as e:
        # Fallback via CMD
        import subprocess
        subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
        return f"🔒 Perintah kunci layar dikirim (Fallback). Detail: {e}"


# Daftar semua tool yang diberikan ke AI
daftar_tools = [
    buka_aplikasi,
    cari_youtube,
    cari_barang_belanja,
    jalankan_perintah_terminal,
    hitung_matematika,
    cek_waktu_sekarang,
    kunci_layar_laptop,
]


# =============================================================
# BAGIAN 2: INISIASI MODEL AI & AGEN
# =============================================================

SYSTEM_PROMPT = """Kamu adalah JARVIS, asisten AI pribadi tingkat lanjut. ATURAN MUTLAK: Kamu HANYA boleh menjawab menggunakan Bahasa Indonesia yang natural, santai, namun profesional. Jangan pernah menggunakan bahasa Inggris dalam memberikan respon, kecuali untuk istilah teknis atau kode komputer.

Kamu memiliki kemampuan untuk mengontrol laptop pengguna secara langsung melalui tools yang tersedia.
Gunakan tools yang sesuai untuk setiap permintaan pengguna.
Kamu memiliki daya ingat dan bisa mengingat percakapan sebelumnya.

TOOLS yang kamu miliki:
- buka_aplikasi: Membuka aplikasi di laptop
- cari_youtube: Mencari/memutar YouTube di browser
- cari_barang_belanja: Mencari/belanja barang di marketplace (Tokopedia/Shopee/Lazada). Gunakan HANYA untuk aktivitas belanja.
- jalankan_perintah_terminal: Menjalankan perintah CMD (terbatas oleh protokol keamanan)
- hitung_matematika: Kalkulator canggih
- cek_waktu_sekarang: Waktu dan tanggal saat ini
- kunci_layar_laptop: Perintah KRITIKAL untuk langsung mengunci layar laptop (Lock OS). JANGAN tertukar dengan belanja.

Jika user meminta untuk mengunci laptop/PC, kamu WAJIB memanggil tool kunci_layar_laptop, bukan tool belanja!
"""

print("[JARVIS] Menghubungkan ke Ollama ...")
try:
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,        # Deterministik penuh → hemat komputasi
        num_predict=256,      # Batasi panjang output agar tidak boros RAM
        num_ctx=2048,         # Context window kecil → jauh lebih ringan
    )
    print(f"[JARVIS] Model '{OLLAMA_MODEL}' siap.\n")
except Exception:
    print(f"[ERROR FATAL] Gagal koneksi ke Ollama!\n{traceback.format_exc()}")
    sys.exit(1)

print("[JARVIS] Membangun agen AI ...")
try:
    if SQLITE_TERSEDIA:
        # Persistent memory — tidak hilang saat bot restart
        import sqlite3
        koneksi_db = sqlite3.connect(DB_PATH, check_same_thread=False)
        memori = SqliteSaver(koneksi_db)
        print(f"[JARVIS] Memory SQLite aktif: {DB_PATH}")
    else:
        memori = MemorySaver()
        print("[JARVIS] Memory RAM aktif (MemorySaver).")

    # Buat trimmer untuk menjaga agar memory (State) tidak terlalu panjang (hindari hallucination bot)
    trimmer = trim_messages(
        max_tokens=6,       # Simpan sekitar 6 pesan terakhir
        strategy="last",
        token_counter=len,  # Menghitung berdasarkan jumlah pesan di list
        include_system=True,# System prompt jangan dihapus
        allow_partial=False,
        start_on="human",   # Selalu mulai chat history dari Human
    )

    def filter_history(state):
        messages = state["messages"]
        last_human_idx = -1
        # Cari index HumanMessage terakhir (penanda satu giliran percakapan / turn)
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].type == "human":
                last_human_idx = i
                break
                
        filtered = []
        for i, m in enumerate(messages):
            # Jika ini adalah pesan SEBELUM turn pengguna saat ini
            if i < last_human_idx:
                # Sembunyikan semua eksekusi Tools dan log-nya agar LLM 1B tidak berhalusinasi mengulangi perintah
                if m.type == "tool":
                    continue
                if m.type == "ai" and getattr(m, "tool_calls", None):
                    continue
            filtered.append(m)
            
        # Terapkan batas max_tokens pada log yang sudah bersih dari tool panggilan masa lalu
        return {"llm_input_messages": trimmer.invoke(filtered)}

    # Gunakan create_react_agent dari langgraph.prebuilt
    mesin_agen = create_react_agent(
        model=llm,
        tools=daftar_tools,
        prompt=SYSTEM_PROMPT,
        pre_model_hook=filter_history,
        checkpointer=memori,
    )
    print("[JARVIS] Agen siap!\n")
except Exception:
    print(f"[ERROR FATAL] Gagal membangun agen!\n{traceback.format_exc()}")
    sys.exit(1)


# =============================================================
# BAGIAN 3: FUNGSI BANTU — PROTOKOL KEAMANAN
# =============================================================

def mengandung_kata_bahaya(teks: str) -> bool:
    """Periksa apakah teks mengandung kata operasi destruktif."""
    teks_lower = teks.lower()
    return any(kata in teks_lower for kata in KATA_BAHAYA)


def validasi_jawaban_keamanan(jawaban_user: str) -> tuple[bool, str]:
    """
    Validasi 3 jawaban verifikasi keamanan dari user.
    Ekspektasi: user mengirim 3 baris → TTL, Kuliah, SMK.
    Return: (semua_benar: bool, pesan_feedback: str)
    """
    baris = [b.strip() for b in jawaban_user.strip().splitlines() if b.strip()]

    if len(baris) < 3:
        return False, (
            "⚠️ Format salah. Kirim 3 jawaban dalam 3 baris terpisah:\n"
            "Baris 1: Tempat tanggal lahir\n"
            "Baris 2: Nama kampus\n"
            "Baris 3: Nama SMK"
        )

    jawaban_ttl    = baris[0].lower()
    jawaban_kuliah = baris[1].lower()
    jawaban_smk    = baris[2].lower()

    salah = []
    if jawaban_ttl    != JAWABAN_VALID["ttl"]:
        salah.append("❌ Jawaban 1 (TTL) salah")
    if jawaban_kuliah != JAWABAN_VALID["kuliah"]:
        salah.append("❌ Jawaban 2 (Kuliah) salah")
    if jawaban_smk    != JAWABAN_VALID["smk"]:
        salah.append("❌ Jawaban 3 (SMK) salah")

    if salah:
        return False, "\n".join(salah)
    return True, "✅ Semua jawaban benar."


PESAN_VERIFIKASI = (
    "🔒 *MODE VERIFIKASI KEAMANAN JARVIS AKTIF*\n\n"
    "Perintah Anda mengandung operasi yang berpotensi destruktif.\n"
    "Untuk melanjutkan, jawab 3 pertanyaan berikut dalam *satu pesan*, pisahkan dengan baris baru:\n\n"
    "1️⃣ Tempat tanggal lahir Anda?\n"
    "2️⃣ Kuliah di mana?\n"
    "3️⃣ SMK di mana?\n\n"
    "_Contoh format jawaban:_\n"
    "`Jakarta, 21 Februari 2006`\n"
    "`Politeknik Industri ATMI`\n"
    "`SMK Ananda Mitra Industri Deltamas`"
)


# =============================================================
# BAGIAN 4: INISIASI TELEGRAM BOT
# =============================================================
print("[JARVIS] Menginisiasi Telegram Bot ...")
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)

# ── Auto-reset: hapus webhook & pending updates lama sebelum polling ──
# Ini mencegah error 409 Conflict saat ada sesi bot sebelumnya yang belum closed
try:
    bot.delete_webhook(drop_pending_updates=True)
    print("[JARVIS] Sesi Telegram lama dibersihkan (webhook + pending updates dihapus).")
except Exception as e:
    print(f"[PERINGATAN] Gagal hapus webhook: {e}")

print("[JARVIS] Telegram Bot siap. Menunggu pesan...\n")




# =============================================================
# HANDLER: /start
# =============================================================
@bot.message_handler(commands=['start', 'mulai'])
def handle_start(message):
    nama = message.from_user.first_name or "Engineer"
    bot.reply_to(message,
        f"⚡ *JARVIS ULTRA* — Proyek Dangerous Human\n\n"
        f"Halo, *{nama}*! Saya siap melayani.\n\n"
        f"🛠️ *Kemampuan saya:*\n"
        f"• Membuka aplikasi di laptop Anda\n"
        f"• Mencari video di YouTube\n"
        f"• Mencari barang di marketplace\n"
        f"• Menjalankan perintah terminal\n"
        f"• Menghitung matematika\n"
        f"• Mengecek waktu\n\n"
        f"📌 *Perintah:*\n"
        f"/reset — Hapus memori percakapan\n"
        f"/status — Cek status sistem\n\n"
        f"Cukup ketik perintah Anda dalam bahasa natural!",
        parse_mode="Markdown"
    )


# =============================================================
# HANDLER: /status
# =============================================================
@bot.message_handler(commands=['status'])
def handle_status(message):
    chat_id     = message.chat.id
    mode_memory = "SQLite (Permanen)" if SQLITE_TERSEDIA else "RAM (Sementara)"
    mode_sec    = user_security_state.get(chat_id, {}).get("mode", "normal")
    bot.reply_to(message,
        f"📊 *Status JARVIS ULTRA*\n\n"
        f"🤖 Model: `{OLLAMA_MODEL}`\n"
        f"💾 Memory: `{mode_memory}`\n"
        f"🔒 Mode keamanan Anda: `{mode_sec}`\n"
        f"⏰ Waktu sistem: `{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}`",
        parse_mode="Markdown"
    )


# =============================================================
# HANDLER: /reset — Reset memori thread user
# =============================================================
@bot.message_handler(commands=['reset', 'lupa'])
def handle_reset(message):
    import uuid
    chat_id = message.chat.id
    # Reset ke thread_id baru → riwayat lama tidak dipakai lagi
    user_thread_map[chat_id] = str(uuid.uuid4())
    # Keluar dari mode verifikasi jika sedang di dalamnya
    user_security_state.pop(chat_id, None)
    bot.reply_to(message, "🔄 Memori percakapan dan status keamanan telah direset.")


# =============================================================
# HANDLER: Semua pesan teks — INTI BOT
# =============================================================
@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_semua_pesan(message):
    chat_id   = message.chat.id
    teks_user = message.text.strip()
    nama_user = message.from_user.username or message.from_user.first_name or str(chat_id)

    print(f"[Pesan] @{nama_user} ({chat_id}): {teks_user}")

    # ── Pastikan user punya thread_id ─────────────────────────
    if chat_id not in user_thread_map:
        user_thread_map[chat_id] = str(chat_id)

    state = user_security_state.get(chat_id, {"mode": "normal"})

    # ══════════════════════════════════════════════════════════
    # CABANG A: User sedang dalam mode verifikasi keamanan
    # ══════════════════════════════════════════════════════════
    if state.get("mode") == "verifikasi":
        lulus, pesan_feedback = validasi_jawaban_keamanan(teks_user)

        if lulus:
            # ── Verifikasi berhasil → eksekusi perintah tertunda ──
            perintah_tertunda = state.get("pending", "")
            user_security_state.pop(chat_id, None)  # Kembali ke mode normal

            bot.reply_to(message,
                f"✅ *Identitas terverifikasi. Akses diberikan.*\n\n"
                f"Menjalankan perintah: `{perintah_tertunda}`",
                parse_mode="Markdown"
            )

            # Eksekusi perintah terminal yang tertunda
            try:
                hasil_eksekusi = subprocess.run(
                    perintah_tertunda,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    encoding='utf-8',
                    errors='replace',
                )
                output = hasil_eksekusi.stdout.strip() or hasil_eksekusi.stderr.strip() or "(Perintah selesai tanpa output)"
                if len(output) > 3000:
                    output = output[:3000] + "\n...(output dipotong)"
                bot.send_message(chat_id, f"📤 *Output Terminal:*\n```\n{output}\n```", parse_mode="Markdown")
            except subprocess.TimeoutExpired:
                bot.send_message(chat_id, "⏱️ Perintah melebihi batas waktu 30 detik dan dihentikan.")
            except Exception as e:
                bot.send_message(chat_id, f"❌ Error eksekusi: {e}")
        else:
            # ── Verifikasi gagal ──────────────────────────────────
            user_security_state.pop(chat_id, None)  # Reset state
            bot.reply_to(message,
                f"🚫 *AKSES DITOLAK — Verifikasi Gagal!*\n\n"
                f"{pesan_feedback}\n\n"
                f"Perintah dibatalkan.",
                parse_mode="Markdown"
            )
        return

    # ══════════════════════════════════════════════════════════
    # CABANG B: Pesan normal — cek kata bahaya
    # ══════════════════════════════════════════════════════════
    if mengandung_kata_bahaya(teks_user):
        # Simpan pesan asli sebagai perintah tertunda, masuk mode verifikasi
        user_security_state[chat_id] = {
            "mode"   : "verifikasi",
            "pending": teks_user,
        }
        bot.reply_to(message, PESAN_VERIFIKASI, parse_mode="Markdown")
        print(f"[SECURITY] @{nama_user} masuk mode verifikasi. Pending: {teks_user}")
        return

    # ══════════════════════════════════════════════════════════
    # CABANG C: Teruskan ke AI Agent
    # ══════════════════════════════════════════════════════════
    bot.send_chat_action(chat_id, 'typing')

    try:
        config = {"configurable": {"thread_id": user_thread_map[chat_id]}}

        hasil = mesin_agen.invoke(
            {"messages": [{"role": "user", "content": teks_user}]},
            config=config,
        )
        jawaban = hasil["messages"][-1].content

    except Exception:
        detail = traceback.format_exc()
        print(f"[ERROR Agent] {detail}")
        jawaban = (
            "⚠️ JARVIS mengalami gangguan saat memproses permintaan Anda.\n"
            "Kemungkinan Ollama timeout atau tidak dapat dijangkau.\n"
            "Silakan coba lagi dalam beberapa saat."
        )

    print(f"[JARVIS] → {jawaban[:120]}{'...' if len(jawaban) > 120 else ''}\n")

    # Kirim balasan — coba reply dulu, fallback ke send_message
    try:
        bot.reply_to(message, jawaban)
    except Exception:
        try:
            # Potong jika terlalu panjang (limit Telegram: 4096 karakter)
            for i in range(0, len(jawaban), 4000):
                bot.send_message(chat_id, jawaban[i:i+4000])
        except Exception as e2:
            bot.send_message(chat_id, f"⚠️ Gagal mengirim balasan lengkap: {e2}")


# =============================================================
# ENTRY POINT
# =============================================================
if __name__ == "__main__":
    print("=" * 65)
    print("  ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗")
    print("  ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝")
    print("  ██║███████║██████╔╝██║   ██║██║███████╗")
    print("  ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║")
    print("  ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║")
    print("  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝")
    print(f"  ULTRA — Dangerous Human Project")
    print(f"  Model   : {OLLAMA_MODEL}")
    print(f"  Memory  : {'SQLite (Permanen)' if SQLITE_TERSEDIA else 'RAM (Sementara)'}")
    print(f"  Security: AKTIF (Protokol Militer)")
    print(f"  Status  : ONLINE — Tekan Ctrl+C untuk berhenti")
    print("=" * 65 + "\n")

    import time
    while True:
        try:
            print("[JARVIS] Polling dimulai ...")
            # skip_pending=True → abaikan pesan lama yang menumpuk saat bot mati
            # restart_on_change tidak ada di telebot, tapi loop while menangani restart otomatis
            bot.infinity_polling(
                timeout=30,
                long_polling_timeout=30,
                skip_pending=True,          # Bersihkan pesan lama saat bot restart
                allowed_updates=["message"],
            )
        except KeyboardInterrupt:
            print("\n[JARVIS] Sistem dimatikan oleh operator. Over and out.")
            break
        except Exception:
            print(f"[ERROR] Polling crash, restart dalam 5 detik...\n{traceback.format_exc()}")
            time.sleep(5)   # Tunggu sebelum reconnect agar konflik instance teratasi
            continue
