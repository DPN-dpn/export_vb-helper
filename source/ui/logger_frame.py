import tkinter as tk

class LoggerFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.text = tk.Text(self, height=10, state="disabled", wrap="none")
        self.text.pack(fill="both", expand=True, padx=10, pady=5)

    def log(self, msg):
        self.text.config(state="normal")
        self.text.insert("end", msg + "\n")
        self.text.see("end")
        self.text.config(state="disabled")