# Ekstraksi Kode: Penambahan Tool Pause Media pada JARVIS ⏯️

**Perintah Instalasi PyAutoGUI:**
```bash
pip install pyautogui
```

## 1. Update pada Fungsi `hard_filter(user_input)`
Tambahkan blok deteksi kata kunci media ini ke dalam fungsi `hard_filter`, sebelum blok `FILTER 10: Lempar ke LangGraph`:

```python
    # ── FILTER 9.5: Kontrol Media (Pause/Play) ──────────────────
    kata_media = ("pause", "jeda", "stop video", "lanjut", "resume", "play lagi")
    if any(k in text for k in kata_media):
        return {
            "action": "tool",
            "tool":   "pause_media",
            "pass_to_llm": False # Membunuh Ghost Loop Llama 1B💥
        }
```

## 2. Update pada Fungsi `run_tool(tool_name, user_input)`
Tambahkan kondisi `elif` ini untuk mengenali perintah *pause_media*. Pastikan letaknya sejajar dengan kondisi `elif` lainnya:

```python
    elif tool_name == "pause_media":
        return tool_pause_media()
```

## 3. Fungsi Eksekutor: `tool_pause_media()`
Tambahkan fungsi ini di bawah fungsi-fungsi tool lainnya (misalnya di bawah `tool_tutup_app`). **Jangan lupa untuk mengimpor pyautogui di bagian atas file Anda (`import pyautogui`).**

```python
import pyautogui 

# ... (kode lainnya) ...

def tool_pause_media() -> str:
    """
    Fungsi untuk mengirimkan sinyal media global (Play/Pause) ke Windows.
    Bekerja seperti menekan tombol Play/Pause di keyboard fisik.
    """
    try:
        # Mengirim sinyal 'playpause' ke sistem operasi
        pyautogui.press('playpause')
        return "Sinyal Play/Pause media berhasil dikirim! ⏯️"
    except Exception as e:
        return f"Gagal mengeksekusi kontrol media. Error: {str(e)}"
```

---
**Catatan Penting:**
Pastikan baris `import pyautogui` diletakkan di bagian paling atas file `jarvis.py` (bersama import bawaan seperti `import os`, `import re`, dll) agar fungsi `tool_pause_media` dapat mengenalinya.
