import tkinter as tk

class Logger:
    def __init__(self, master=None):
        self.text = tk.Text(height=10, state="disabled", wrap="none")

    def attach(self, master):
        self.text.pack(fill="both", padx=10, pady=(5, 10), side="bottom")

    def log(self, msg):
        self.text.config(state="normal")
        self.text.insert("end", msg + "\n")
        self.text.see("end")
        self.text.config(state="disabled")