import os
import re
import subprocess
import webbrowser
import pyautogui
from ollama import Client
from telebot import TeleBot

# ════════════════════════════════
# INISIALISASI
# ════════════════════════════════
bot    = TeleBot("8602266927:AAGG90PmI0697sy4tDRsRiKA0qrebe0Y3yQ")
client = Client()

try:
    bot.delete_webhook(drop_pending_updates=True)
    print("Sesi Telegram lama dibersihkan (menghindari error 409).")
except Exception as e:
    print(f"Gagal hapus webhook: {e}")

# ════════════════════════════════
# DATABASE APLIKASI
# ════════════════════════════════
DB_APP = {
    "roblox": {
        "path": os.path.expandvars(r"%LOCALAPPDATA%\Roblox\Versions\RobloxPlayerLauncher.exe"),
        "exe":  "RobloxPlayerBeta.exe"
    },
    "epic": {
        "path": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
        "exe":  "EpicGamesLauncher.exe"
    },
    "epic store": {
        "path": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
        "exe":  "EpicGamesLauncher.exe"
    },
    "brave": {
        "path": "brave",
        "exe":  "brave.exe"
    }
}

# ════════════════════════════════
# SYSTEM PROMPT
# ════════════════════════════════
system_prompt = """
Kamu adalah AI assistant lokal bernama "Jarvis".
Kamu berkomunikasi via Telegram dan mengontrol laptop user.

═══════════════════════════════════════
BAHASA
═══════════════════════════════════════
- Balas dalam bahasa yang sama dengan user
- Jawab singkat dan padat, maksimal 2 kalimat
- Jangan panjang lebar

═══════════════════════════════════════
PRE-FILTER WAJIB — URUTAN INI TIDAK BOLEH DILANGGAR
═══════════════════════════════════════
Cek input user dari atas ke bawah, BERHENTI di langkah pertama yang cocok:

LANGKAH 1 — SAPAAN?
  Kata: hi, hello, halo, hai, hey, hei, pagi, siang, malam, oke, ok,
        thanks, makasih, sip, mantap, iya, ya, tidak, nggak, done
  → Balas teks singkat. STOP. Jangan lanjut.

LANGKAH 2 — PERTANYAAN?
  Ada tanda tanya? Atau dimulai dengan: apa, siapa, kenapa, bagaimana,
  berapa, dimana, kapan, apakah, gimana
  → Jawab dengan teks. STOP. Jangan panggil tool apapun.

LANGKAH 3 — PERINTAH MATEMATIKA?
  Ada kata: hitung, berapa hasil, kalkulasi, tambah, kurang, kali, bagi
  DAN ada angka di kalimat
  → Panggil tool MATEMATIKA saja. STOP.

LANGKAH 4 — PERINTAH YOUTUBE?
  Ada kata: putar, play, buka youtube, tonton, dengerin
  DAN ada judul/nama lagu/video
  → Panggil tool YOUTUBE saja. STOP.

LANGKAH 5 — PERINTAH KUNCI?
  Kalimat PERSIS berisi: kunci laptop, lock laptop, kunci layar, lock screen
  → Panggil tool KUNCI saja. STOP.

LANGKAH 6 — PERINTAH MATIKAN LAPTOP?
  Kalimat PERSIS berisi: matikan laptop, shutdown, turn off
  → Panggil tool SHUTDOWN saja. STOP.

LANGKAH 7 — BUKA APLIKASI?
  Ada kata: buka, open, jalankan
  DAN ada nama aplikasi yang dikenal: roblox, epic, epic store, brave
  → Panggil tool BUKA_APP saja. STOP.

LANGKAH 8 — TUTUP APLIKASI?
  Ada kata: tutup, close, matikan aplikasi, kill
  DAN ada nama aplikasi
  → Panggil tool TUTUP_APP saja. STOP.

LANGKAH 9 — TIDAK ADA YANG COCOK?
  → Balas: "Maaf, aku tidak mengerti. Coba ulangi dengan lebih spesifik."
  → JANGAN panggil tool apapun.

═══════════════════════════════════════
LARANGAN ABSOLUT
═══════════════════════════════════════
❌ JANGAN buka e-commerce / toko online apapun
❌ JANGAN gunakan perintah lama untuk memicu tool sekarang
❌ JANGAN panggil tool jika tidak ada perintah eksplisit
❌ JANGAN panggil lebih dari 1 tool sekaligus
❌ JANGAN berasumsi — jika ragu, tanya balik

═══════════════════════════════════════
CONTOH BENAR vs SALAH
═══════════════════════════════════════
User: "hi"              → "Halo! Ada yang bisa dibantu?" [BUKAN buka YouTube]
User: "oke"             → "Siap!" [BUKAN jalankan perintah sebelumnya]
User: "matikan"         → "Maksudnya matikan laptop?" [TANYA BALIK]
User: "matikan laptop"  → [tool SHUTDOWN] ✅
User: "beli laptop"     → "Maaf, aku tidak bisa membuka toko online." ✅
User: "putar spotify"   → "Maaf, aku hanya bisa putar YouTube saat ini." ✅
User: "buka roblox"     → [tool BUKA_APP → roblox] ✅
User: "tutup brave"     → [tool TUTUP_APP → brave] ✅
User: "buka shopee"     → "Maaf, aku tidak bisa membuka toko online." ✅

═══════════════════════════════════════
JIKA TIDAK YAKIN
═══════════════════════════════════════
Tanya balik: "Maksudnya [ulang kata user]?"
Jangan pernah asal action.
"""

# ════════════════════════════════
# HARD FILTER — JALAN SEBELUM LLM
# ════════════════════════════════
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

LARANGAN = (
    "tokopedia", "shopee", "lazada", "bukalapak",
    "blibli", "amazon", "beli", "order", "belanja",
    "checkout", "keranjang", "toko"
)

def hard_filter(user_input: str) -> dict:
    text  = user_input.lower().strip()
    words = set(text.split())

    # ── FILTER 1: Sapaan ──────────────────────────
    if text in SAPAAN or words.issubset(SAPAAN):
        return {
            "action": "direct_reply",
            "reply":  "Halo! Ada yang bisa dibantu?",
            "pass_to_llm": False
        }

    # ── FILTER 2: Larangan absolut ────────────────
    if any(kata in text for kata in LARANGAN):
        return {
            "action": "direct_reply",
            "reply":  "Maaf, aku tidak bisa membuka toko online atau membantu belanja.",
            "pass_to_llm": False
        }

    # ── FILTER 3: Pertanyaan ──────────────────────
    if text.endswith("?") or text.startswith(KATA_TANYA):
        return {
            "action": "direct_reply",
            "reply":  None,
            "pass_to_llm": True,
            "no_tool": True
        }

    # ── FILTER 4: Matematika ──────────────────────
    kata_math = ("hitung", "berapa hasil", "kalkulasi")
    ada_angka  = bool(re.search(r'\d', text))
    if any(k in text for k in kata_math) and ada_angka:
        return {
            "action": "tool",
            "tool":   "matematika",
            "pass_to_llm": False
        }

    # ── FILTER 5: YouTube ─────────────────────────
    kata_yt = ("putar", "play", "buka youtube", "tonton", "dengerin")
    if any(k in text for k in kata_yt):
        return {
            "action": "tool",
            "tool":   "youtube",
            "pass_to_llm": False
        }

    # ── FILTER 6: Kunci ───────────────────────────
    kata_kunci = ("kunci laptop", "lock laptop", "kunci layar", "lock screen")
    if any(k in text for k in kata_kunci):
        return {
            "action": "tool",
            "tool":   "kunci",
            "pass_to_llm": False
        }

    # ── FILTER 7: Shutdown ────────────────────────
    kata_off = ("matikan laptop", "shutdown", "turn off")
    if any(k in text for k in kata_off):
        return {
            "action": "tool",
            "tool":   "shutdown",
            "pass_to_llm": False
        }

    # ── FILTER 8: Buka Aplikasi ───────────────────
    kata_buka = ("buka ", "open ", "jalankan ")
    if any(k in text for k in kata_buka) and "youtube" not in text:
        return {
            "action": "tool",
            "tool":   "buka_app",
            "pass_to_llm": False
        }

    # ── FILTER 9: Tutup Aplikasi ──────────────────
    kata_tutup = ("tutup ", "close ", "matikan aplikasi", "kill ")
    if any(k in text for k in kata_tutup):
        return {
            "action": "tool",
            "tool":   "tutup_app",
            "pass_to_llm": False
        }

    # ── FILTER 9.5: Kontrol Media (Pause/Play) ──────────────────
    kata_media = ("pause", "jeda", "stop video", "lanjut", "resume", "play lagi")
    if any(k in text for k in kata_media):
        return {
            "action": "tool",
            "tool":   "pause_media",
            "pass_to_llm": False
        }

    # ── FILTER 10: Lempar ke LangGraph ────────────
    return {
        "action": "unknown",
        "pass_to_llm": True
    }

# ════════════════════════════════
# TOOL RUNNER
# ════════════════════════════════
def run_tool(tool_name: str, user_input: str) -> str:
    if tool_name == "matematika":
        return tool_matematika(user_input)
    elif tool_name == "youtube":
        return tool_youtube(user_input)
    elif tool_name == "kunci":
        return tool_kunci()
    elif tool_name == "shutdown":
        return tool_shutdown()
    elif tool_name == "buka_app":
        return tool_buka_app(user_input)
    elif tool_name == "tutup_app":
        return tool_tutup_app(user_input)
    elif tool_name == "pause_media":
        return tool_pause_media()
    return "Tool tidak ditemukan."

def tool_matematika(expr: str) -> str:
    try:
        angka = re.findall(r'[\d+\-*/().]+', expr)
        hasil = eval(" ".join(angka))
        return f"Hasilnya: {hasil}"
    except:
        return "Tidak bisa menghitung ekspresi itu."

def tool_youtube(query: str) -> str:
    kata_hapus = ("putar", "play", "tonton", "dengerin", "di youtube", "youtube")
    q = query.lower()
    for k in kata_hapus:
        q = q.replace(k, "")
    q   = q.strip()
    url = f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Membuka YouTube untuk: {q}"

def tool_kunci() -> str:
    subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
    return "Laptop dikunci."

def tool_shutdown() -> str:
    subprocess.run(["shutdown", "/s", "/t", "10"])
    return "Laptop akan mati dalam 10 detik. Ketik 'batal shutdown' untuk membatalkan."

def tool_buka_app(query: str) -> str:
    q = query.lower()
    for k in ["tolong ", "dong", "coba ", "jarvis ", "buka ", "open ", "jalankan "]:
        q = q.replace(k, "")
    nama_app = q.strip()

    if nama_app in DB_APP:
        app_path = DB_APP[nama_app]["path"]
        try:
            if ":" in app_path or "\\" in app_path:
                os.startfile(app_path)
            else:
                os.system(f"start {app_path}")
            return f"Siap Bos! Membuka {nama_app.title()}..."
        except:
            return f"Gagal membuka {nama_app}. Path-nya mungkin salah atau aplikasinya belum diinstall."
    else:
        os.system(f"start {nama_app}")
        return f"Mencoba membuka {nama_app.title()}..."

def tool_tutup_app(query: str) -> str:
    q = query.lower()
    for k in ["tolong ", "dong", "coba ", "jarvis ", "tutup ", "close ", "matikan aplikasi ", "kill "]:
        q = q.replace(k, "")
    nama_app = q.strip()

    exe_name = DB_APP[nama_app]["exe"] if nama_app in DB_APP else f"{nama_app}.exe"
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", exe_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return f"Aplikasi {nama_app.title()} berhasil dimatikan!"
    except:
        return f"Gagal mematikan {nama_app}. Mungkin aplikasinya belum terbuka."

def tool_pause_media() -> str:
    try:
        pyautogui.press('playpause')
        return "Sinyal Play/Pause media berhasil dikirim! ⏯️"
    except Exception as e:
        return f"Gagal mengeksekusi kontrol media. Error: {str(e)}"

# ════════════════════════════════
# LLM FALLBACK
# Dipanggil HANYA kalau filter
# tidak bisa handle
# ════════════════════════════════
def tanya_llm(user_input: str, no_tool: bool = False) -> str:
    tambahan = "\nPENTING: Balas dengan TEKS SAJA. JANGAN panggil tool apapun." if no_tool else ""
    response  = client.chat(
        model="llama3.2:1b",
        messages=[
            {"role": "system", "content": system_prompt + tambahan},
            {"role": "user",   "content": user_input}
        ]
    )
    return response['message']['content']

# ════════════════════════════════
# TELEGRAM HANDLER — LOGIC UTAMA
# ════════════════════════════════
@bot.message_handler(func=lambda message: True)
def handle_telegram_message(message):
    user_input = message.text
    chat_id    = message.chat.id

    # STEP 1 ── Hard Filter dulu
    hasil_filter = hard_filter(user_input)

    # STEP 2 ── Filter handle sendiri → LLM tidak dipanggil
    if not hasil_filter["pass_to_llm"]:

        if hasil_filter["action"] == "direct_reply":
            bot.send_message(chat_id, hasil_filter["reply"])

        elif hasil_filter["action"] == "tool":
            respon_tool = run_tool(hasil_filter["tool"], user_input)
            bot.send_message(chat_id, respon_tool)

        return  # ← STOP, LangGraph tidak dipanggil

    # STEP 3 ── Filter tidak bisa handle → LLM / LangGraph
    else:
        if hasil_filter.get("no_tool"):
            # Pertanyaan biasa → LLM jawab teks saja
            respon = tanya_llm(user_input, no_tool=True)
            bot.send_message(chat_id, respon)
        else:
            # Unknown / kompleks → sambungkan ke LangGraph kamu
            # respon = agen_langgraph_lu.invoke({"input": user_input})
            # bot.send_message(chat_id, respon["output"])

            # Sementara fallback ke LLM biasa
            respon = tanya_llm(user_input)
            bot.send_message(chat_id, respon)

# ════════════════════════════════
# JALANKAN BOT
# ════════════════════════════════
if __name__ == "__main__":
    print("Jarvis aktif...")
    bot.polling(none_stop=True)
