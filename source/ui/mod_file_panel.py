import tkinter as tk
import os

class ModFileListPanel(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        tk.Label(self, text="모드 파일 목록").pack()
        self.listbox = tk.Listbox(self, height=30, width=60)
        self.listbox.pack(fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.on_file_selected)

        self.listbox.bind("<Double-Button-1>", self.on_file_activate)
        self.listbox.bind("<Return>", self.on_file_activate)

    def set_file_list(self, file_list):
        self.listbox.delete(0, tk.END)
        for fname in sorted(set(file_list)):
            if fname.lower().endswith((".ib", ".buf")):
                self.listbox.insert(tk.END, os.path.basename(fname))

    def on_file_selected(self, event):
        sel = self.listbox.curselection()
        if sel:
            self.controller.set_selected_file(self.listbox.get(sel[0]))
            
    def on_file_activate(self, event):
        sel = self.listbox.curselection()
        if sel:
            fname = self.listbox.get(sel[0])
            self.controller.set_selected_file(fname)
            self.controller.assign_selected_file()