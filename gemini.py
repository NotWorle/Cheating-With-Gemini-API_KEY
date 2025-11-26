# Read API KEY
from dotenv import load_dotenv
load_dotenv()  # đọc file .env

import google.generativeai as genai
import os
import sys
import time
import shutil
from pynput import keyboard
from PIL import Image
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import pyperclip
import tkinter as tk
from tkinter import messagebox
from functools import wraps
import inspect

API_KEY = None
SCREENSHOT_FOLDER = r"C:\Users\Huy Le\Pictures\skibidi"


def resource_path(relative_path):
    """ Lấy đường dẫn đúng khi chạy .exe hoặc chạy Python """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def key_api_validation(func):
    sig = inspect.signature(func)
    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        key = bound.arguments.get('key')

        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            model.generate_content("ping")   # request test
            return func(*args, **kwargs)
        except Exception as e:
            raise ValueError(f'API is invalid: {key}')
    return wrapper

@key_api_validation
def set_key(key):
    global API_KEY
    API_KEY = key

    
# api_key = os.getenv("GEMINI_API_KEY")
def ui_apikey(env=None)-> bool:
    def set_key_ui():
        key = entry_key.get()
        try:
            set_key(key)
            result['status'] = True
            root.destroy()
        except ValueError as e:
            print('Lôi')
            messagebox.showerror("Lỗi", "Key nhập không hợp lệ!")

    result = {"status": False}  # biến để biết user nhập đúng hay tắt cửa sổ

    # For developer
    if env:
        key = os.getenv(env)
        set_key(key)
        return True
    else: # For user
        root = tk.Tk()
        root.title('Love Window')
        root.geometry("400x300")

        tk.Label(root, text="Nhập key: ").pack()
        entry_key = tk.Entry(root)
        entry_key.pack()
     
        tk.Button(root, text="Nhập", command=set_key_ui).pack(pady=10)

        root.mainloop()
    return result["status"]

def stop_program(key):
    global runing
    if key == keyboard.Key.esc:
        runing = False
        remove_all_in_folder(SCREENSHOT_FOLDER)
    os.system("taskkill /IM cmd.exe /F")

def remove_all_in_folder(path):
    for item in os.listdir(path):
        item_path = os.path.join(path, item)

        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)


def ask_gemini(image_path):
    time.sleep(5)
    img = Image.open(image_path)
    prompt = "Bạn là một chuyên gia phân tích đề thi trắc nghiệm. Đọc ảnh thật là kỹ, suy nghĩ logic và chọn đáp án đúng nhất, chỉ cần trả lời bằng 1 từ A, B, C, hoặc D."
    response = model.generate_content([prompt, img])
    return response.text
    
class ScreenshotHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith((".png", ".jpg", ".jpeg")):
            print("Ảnh mới phát hiện:", event.src_path)

            answer = ask_gemini(event.src_path)
            print("Gemini trả lời:", answer)

            # copy vào clipboard
            pyperclip.copy(answer)
            print("Đã copy kết quả vào clipboard (Ctrl+V để dán).")

runing = True
if __name__ == "__main__":
    # User Interface for input key
    if ui_apikey('GEMINI_API_KEY'):
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        event_handler = ScreenshotHandler()
        observer = Observer()
        observer.schedule(event_handler, SCREENSHOT_FOLDER, recursive=False)
        observer.start()
        print("Đang theo dõi ảnh màn hình...")

        listener = keyboard.Listener(on_press=stop_program)
        listener.start()
        try:
            while True:
                if not runing:
                    sys.exit(0)
                time.sleep(0.2)  # tránh tốn CPU
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    