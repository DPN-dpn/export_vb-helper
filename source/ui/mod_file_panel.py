import tkinter as tk
import os


class ModFileListPanel(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.full_file_list = []  # 전체 파일 목록 저장

        # 🔍 필터 입력창 (라벨 + 입력창)
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", self.update_filtered_list)
        filter_frame = tk.Frame(self)
        filter_frame.pack(fill="x", padx=2, pady=2)
        tk.Label(filter_frame, text="🔍").pack(side="left", padx=(0, 6))
        tk.Entry(filter_frame, textvariable=self.filter_var).pack(
            side="left", fill="x", expand=True
        )

        # 📜 리스트박스 — 컨테이너 가득 채우도록 설정
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill="both", expand=True, padx=2, pady=2)
        self.listbox.bind("<<ListboxSelect>>", self.on_file_selected)
        self.listbox.bind("<Double-Button-1>", self.on_file_activate)
        self.listbox.bind("<Return>", self.on_file_activate)

    def set_file_list(self, file_list):
        self.full_file_list = sorted(set(file_list))  # 전체 저장
        self.update_filtered_list()

    def update_filtered_list(self, *args):
        keyword = self.filter_var.get().lower()
        self.listbox.delete(0, tk.END)
        for fname in self.full_file_list:
            if fname.lower().endswith((".ib", ".buf")) and keyword in fname.lower():
                self.listbox.insert(tk.END, fname)

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
