import tkinter as tk

class Logger:
    def __init__(self, master):
        print("[logger.py] Logger 초기화")
        self.text = tk.Text(master, height=6, state="disabled", wrap="none")
        self.v_scroll = tk.Scrollbar(master, orient="vertical", command=self.text.yview)
        self.h_scroll = tk.Scrollbar(master, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

    def get_widget(self):
        print("[logger.py] get_widget 호출")
        return self.text, self.v_scroll, self.h_scroll

    def log(self, message):
        print(f"[logger] {message}")
        self.text.config(state="normal")
        self.text.insert("end", message + "\n")
        self.text.see("end")
        self.text.config(state="disabled")