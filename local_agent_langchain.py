import datetime
import math
import traceback
import sys

# Fix encoding untuk terminal Windows agar tidak error saat menampilkan teks
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# PAKET BARU: langchain-ollama (versi terbaru, bukan community)
# pip install -U langchain-ollama
# ============================================================
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain.tools import tool


# ==========================================
# 1. DEFINISI TOOLS (ALAT BANTU UNTUK AI)
# ==========================================

@tool
def hitung_matematika(ekspresi: str) -> str:
    """Gunakan tool ini HANYA ketika Anda perlu menghitung operasi matematika yang rumit.
    Masukkan ekspresi matematika dalam format Python (contoh: '25 * 4' atau '100 / 3')."""
    try:
        hasil = eval(ekspresi, {"__builtins__": None}, {"math": math})
        return str(hasil)
    except Exception as e:
        return f"Error saat menghitung: {e}"

@tool
def cek_waktu_sekarang(query: str = "") -> str:
    """Gunakan tool ini secara spesifik jika manusia menanyakan tentang waktu, tanggal, jam, atau hari ini."""
    sekarang = datetime.datetime.now()
    return sekarang.strftime("%A, %d-%m-%Y %H:%M:%S")

# Kumpulkan semua tool ke dalam satu list
daftar_tools = [hitung_matematika, cek_waktu_sekarang]


# ==========================================
# 2. INISIASI MODEL AI LOKAL (OLLAMA + QWEN)
# ==========================================
print("[Sistem] Menghubungkan ke Ollama di http://localhost:11434 ...")

try:
    llm = ChatOllama(
        model="qwen3.5",           # Nama model yang terinstal di Ollama Anda
        base_url="http://localhost:11434",
        temperature=0.1,
    )
    print("[Sistem] Koneksi berhasil! Model qwen3.5 siap.")
except Exception as e:
    print(f"[ERROR] Gagal menginisiasi model!\n{traceback.format_exc()}")
    exit(1)


# ==========================================
# 3. INSTRUKSI SISTEM UNTUK AI
# ==========================================
template_instruksi = (
    "Kamu adalah AI asisten cerdas dalam proyek 'Dangerous Human'. "
    "Jawablah pertanyaan manusia sebaik dan setepat mungkin dalam bahasa Indonesia. "
    "Gunakan tool yang tersedia jika dibutuhkan."
)


# ==========================================
# 4. MEMBUAT AGEN
# ==========================================
print("[Sistem] Membangun agen AI ...")
try:
    mesin_agen = create_agent(
        model=llm,
        tools=daftar_tools,
        system_prompt=template_instruksi,
    )
    print("[Sistem] Agen siap digunakan!\n")
except Exception as e:
    print(f"[ERROR] Gagal membangun agen!\n{traceback.format_exc()}")
    exit(1)


# ==========================================
# 5. LOOP TERMINAL UTAMA (INTERAKSI USER)
# ==========================================
def mulai_sistem():
    print("=" * 60)
    print("[AI AGENT] Agent Kecerdasan Lokal (LangChain + Qwen) Aktif!")
    print("   Proyek   : Dangerous Human")
    print("   Perintah : Ketik 'keluar' untuk mematikan mesin.")
    print("=" * 60)

    while True:
        try:
            teks_input = input("\n[Pengguna] : ")

            if teks_input.lower() in ['keluar', 'exit', 'quit']:
                print("\n[Sistem] Mematikan sistem inti... Sampai jumpa, Engineer!")
                break

            if teks_input.strip() == "":
                continue

            print("\n[Agent sedang memproses keputusan...]")

            # Kirim pesan ke agen dalam format messages terbaru
            jawaban = mesin_agen.invoke({
                "messages": [{"role": "user", "content": teks_input}]
            })

            # Ambil teks jawaban dari pesan terakhir
            hasil_teks = jawaban["messages"][-1].content

            print("\n" + "=" * 50)
            print(f"[Agent] : {hasil_teks}")
            print("=" * 50)

        except KeyboardInterrupt:
            print("\n\n[Sistem] Mesin dihentikan paksa. Over and out!")
            break
        except Exception as e:
            # Tampilkan FULL traceback agar mudah debug
            print(f"\n[Sistem Error - Detail Lengkap]:")
            traceback.print_exc()

if __name__ == "__main__":
    mulai_sistem()
