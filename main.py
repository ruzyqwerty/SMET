import tkinter as tk
import tkinter.font as tkFont
import textwrap
import keyboard
import mss
from PIL import Image, ImageOps
from deep_translator import GoogleTranslator
import pytesseract
import os


pytesseract.pytesseract.tesseract_cmd = r"D:\Programs\Tesseract-OCR\tesseract.exe"


def translate_text(text, src='en', dest='ru'):
    try:
        translated = GoogleTranslator(source=src, target=dest).translate(text)
    except Exception as e:
        print("Ошибка перевода:", e)
        translated = "[ошибка перевода]"
    print("\n--- Перевод ---\n", translated, sep='')
    return translated


def ocr_image(path="preprocessed.png"):
    from PIL import Image
    img = Image.open(path)
    text = pytesseract.image_to_string(img, lang='eng')

    # Удаляем лишние переводы строк, оставляем только пробелы
    cleaned_text = " ".join(line.strip() for line in text.splitlines() if line.strip())
    print("\n--- Распознанный текст ---\n", cleaned_text)
    return cleaned_text


def show_popup(text, x, y, max_width_px):
    popup = tk.Tk()
    popup.overrideredirect(True)
    popup.attributes("-alpha", 0.9)
    popup.attributes("-topmost", True)

    # Шрифт и параметры
    font = tkFont.Font(family="Arial", size=14)
    padding = 20
    max_win_width = min(600, max_width_px)
    max_win_height = 400

    # Оценка символов в строке
    avg_char_width = font.measure("n")
    max_chars_per_line = max(10, (max_win_width - padding) // avg_char_width)

    # Обёртка текста
    wrapped_text = textwrap.fill(text, width=max_chars_per_line)
    lines = wrapped_text.splitlines()

    line_height = font.metrics("linespace")
    text_width = font.measure(max(lines, key=len)) + padding
    text_height = line_height * len(lines) + padding

    window_width = max(160, min(text_width, max_win_width))
    window_height = min(text_height, max_win_height)

    # Позиция: не выходить за экран
    screen_w = popup.winfo_screenwidth()
    screen_h = popup.winfo_screenheight()
    x = min(max(0, x), screen_w - window_width)
    y = min(max(0, y), screen_h - window_height)

    popup.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Закрытие
    popup.bind("<Escape>", lambda e: popup.destroy())
    popup.bind("<Button-1>", lambda e: popup.destroy())

    # ===== scrollable Text =====
    frame = tk.Frame(popup)
    frame.pack(fill="both", expand=True)

    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")

    text_widget = tk.Text(
        frame,
        wrap="word",
        font=font,
        bg="white",
        fg="black",
        padx=10,
        pady=10,
        yscrollcommand=scrollbar.set
    )
    text_widget.insert("1.0", wrapped_text)
    text_widget.config(state="disabled")
    text_widget.pack(fill="both", expand=True)

    scrollbar.config(command=text_widget.yview)

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

    os.remove("screenshot.png")
    os.remove("preprocessed.png")

    if translated == "":
        return

    show_popup(translated, x1, y1, x2 - x1)


keyboard.add_hotkey('f9', select_area_and_screenshot)

print("Нажми F9 для запуска. ПКМ — отмена.")
keyboard.wait()
