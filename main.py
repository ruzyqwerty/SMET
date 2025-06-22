import tkinter as tk
import keyboard
import mss
from PIL import Image, ImageOps
from deep_translator import GoogleTranslator
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"



def translate_text(text, src='en', dest='ru'):
    translated = GoogleTranslator(source=src, target=dest).translate(text)
    print("\n--- Перевод ---\n", translated)
    return translated


def ocr_image(path="preprocessed.png"):
    from PIL import Image
    img = Image.open(path)
    text = pytesseract.image_to_string(img, lang='eng')
    print("\n--- Распознанный текст ---\n", text, sep='')
    return text.strip()


def show_popup(text):
    popup = tk.Tk()
    popup.title("Перевод")
    popup.attributes("-topmost", True)
    popup.geometry("600x300")

    # Автоматическое закрытие по ESC или клику
    popup.bind("<Escape>", lambda e: popup.destroy())
    popup.bind("<Button-1>", lambda e: popup.destroy())

    # Текстовое поле
    label = tk.Text(popup, wrap="word", font=("Arial", 14), padx=10, pady=10)
    label.insert("1.0", text)
    label.config(state="disabled", bg="white")
    label.pack(expand=True, fill="both")

    popup.mainloop()


def select_area_and_screenshot():
    coords = {'x1': None, 'y1': None, 'x2': None, 'y2': None}
    was_canceled = {'flag': False}

    def cancel(event=None):
        was_canceled['flag'] = True
        print("Выделение отменено (ESC)")
        root.quit()

    def on_mouse_down(event):
        if was_canceled['flag']:
            return
        coords['x1'], coords['y1'] = event.x_root, event.y_root
        canvas.delete("rect")

    def on_mouse_drag(event):
        if was_canceled['flag']:
            return
        coords['x2'], coords['y2'] = event.x_root, event.y_root
        canvas.delete("rect")
        canvas.create_rectangle(
            coords['x1'], coords['y1'],
            coords['x2'], coords['y2'],
            outline='red', width=2, tags="rect"
        )

    def on_mouse_up(event):
        if was_canceled['flag']:
            return
        coords['x2'], coords['y2'] = event.x_root, event.y_root
        root.quit()

    screen = mss.mss().monitors[1]
    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry(f"{screen['width']}x{screen['height']}+0+0")
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.3)
    root.configure(bg='black')

    root.focus_force()

    canvas = tk.Canvas(root, cursor="cross")
    canvas.pack(fill=tk.BOTH, expand=True)

    canvas.bind("<Button-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_drag)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)
    canvas.bind("<Button-3>", cancel)

    root.mainloop()
    root.destroy()

    if was_canceled['flag']:
        return

    if None in coords.values():
        select_area_and_screenshot()
        return

    x1 = min(coords['x1'], coords['x2'])
    y1 = min(coords['y1'], coords['y2'])
    x2 = max(coords['x1'], coords['x2'])
    y2 = max(coords['y1'], coords['y2'])

    if x2 - x1 < 5 or y2 - y1 < 5:
        print("Слишком маленькая область.")
        return

    with mss.mss() as sct:
        monitor = {"top": y1, "left": x1, "width": x2 - x1, "height": y2 - y1}
        img = sct.grab(monitor)
        Image.frombytes("RGB", img.size, img.rgb).save("screenshot.png")

    img = Image.open("screenshot.png").convert("L")
    img = ImageOps.autocontrast(img)
    img = img.resize((img.width * 2, img.height * 2))
    img.save("preprocessed.png")

    text = ocr_image("preprocessed.png")
    translated = translate_text(text)
    show_popup(translated)


keyboard.add_hotkey('f9', select_area_and_screenshot)

print("Нажми F9 для запуска. ПКМ — отмена.")
keyboard.wait()
