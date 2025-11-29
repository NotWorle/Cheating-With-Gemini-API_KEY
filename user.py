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


# def resource_path(relative_path):
#     """ Lấy đường dẫn đúng khi chạy .exe hoặc chạy Python """
#     try:
#         base_path = sys._MEIPASS
#     except Exception:
#         base_path = os.path.abspath(".")
#     return os.path.join(base_path, relative_path)

def key_api_validation(func):
    sig = inspect.signature(func)
    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        key = bound.arguments.get('key')

        if not key or key.strip() == "":
            raise ValueError("API key trống!")

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

def set_filepath(filepath:str):
    if os.path.exists(filepath):
        global SCREENSHOT_FOLDER
        SCREENSHOT_FOLDER = filepath
        return True
    raise ValueError(f'File path: {filepath} isn\'t existed')

    
def ui_apikey()-> bool:
    def ui_set_key():
        key = entry_key.get()
        try:
            set_key(key)
            result['status_key'] = True
            messagebox.showinfo("Thành công", "Key hợp lệ!")
        except ValueError as e:
            print('Lôi')
            messagebox.showerror("Lỗi", e)

    def ui_set_filepath():
        filepath = entry_filepath.get()
        print(filepath)
        try:
            set_filepath(filepath)
            result['status_filepath'] = True
            messagebox.showinfo("Thành công", "Filepath hợp lệ!")

        except Exception as e:
            messagebox.showerror("ERROR", e)

    def on_click_check_key():
        ui_set_key()
        check_result()

    def on_click_check_filepath():
        ui_set_filepath()
        check_result()

    def check_result():
        if all(i for i in result.values()):
            root.destroy()

    result = {
        "status_key": False,
        "status_filepath": False
        }  # biến để biết user nhập đúng hay tắt cửa sổ


    # For developer
    
    root = tk.Tk()
    root.title('Love Window')
    root.geometry("400x300")

    tk.Label(root, text="Nhập key: ").pack()
    entry_key = tk.Entry(root)
    entry_key.pack()
    tk.Button(root, text="Kiểm tra key", command=on_click_check_key).pack(pady=10)

    tk.Label(root, text="Nhập đường dẫn: ").pack()
    entry_filepath = tk.Entry(root)
    entry_filepath.pack()
    tk.Button(root, text="Kiểm filepath", command=on_click_check_filepath).pack(pady=10)

    root.mainloop()

    return all(i for i in result.values())

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
    prompt = "Bạn là một chuyên gia phân tích đề thi trắc nghiệm và tự luận. Đọc ảnh thật là kỹ, suy nghĩ logic và chọn đáp án đúng nhất." \
    "Kết hợp suy nghĩ sâu, tìm kiếm website về môn liên quan. Trả lời gọn xúc tích, nhưng đầy đủ ý. Đối với trắc nghiệm hãy đặt A,B... là từ cuối cùng"
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
    if ui_apikey():
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
    