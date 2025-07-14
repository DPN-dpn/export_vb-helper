import tkinter as tk
from common import REQUIRED_COMPONENT_KEYS

class ComponentSlotPanel(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        self.canvas = tk.Canvas(self)
        self.inner_frame = tk.Frame(self.canvas)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.bind("<Configure>", self._resize_inner_frame)

        self.component_widgets = []  # 각 컴포넌트의 {key: stringvar, ...}
        self.slot_labels = []        # 선택 시 강조할 label 모음
        self.selected_index = None
        self.selected_key = None

    def display_components(self, components, mod_files_by_type):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.component_widgets.clear()
        self.slot_labels.clear()

        for idx, comp in enumerate(components):
            group = tk.LabelFrame(self.inner_frame, text=comp.get("name", f"컴포넌트 {idx+1}"))
            group.pack(fill="x", padx=10, pady=5, expand=True)

            widget_row = {}

            for key in REQUIRED_COMPONENT_KEYS:
                row = tk.Frame(group)
                row.pack(fill="x", pady=2, expand=True)

                def make_click_handler(i, k):
                    return lambda e: self.select_slot(i, k)

                # 슬롯 키 라벨
                key_label = tk.Label(row, text=key, width=12)
                key_label.pack(side="left")
                key_label.bind("<Button-1>", make_click_handler(idx, key))

                # 해시 라벨
                hash_val = comp.get(key) or ""
                hash_label = tk.Label(row, text=hash_val, width=15, anchor="w", bg="#f0f0f0")
                hash_label.pack(side="left", padx=5)
                hash_label.bind("<Button-1>", make_click_handler(idx, key))

                # 선택된 파일명 표시 라벨
                val = tk.StringVar(value="")
                file_label = tk.Label(row, textvariable=val, anchor="w", bg="#f7f7f7", relief="sunken")
                file_label.pack(side="left", padx=5, expand=True, fill="x")
                file_label.bind("<Button-1>", make_click_handler(idx, key))

                # 선택 강조용으로 기억
                self.slot_labels.append((idx, key, key_label, hash_label, file_label))
                widget_row[key] = val

            self.component_widgets.append(widget_row)

    def select_slot(self, index, key):
        # 이전 선택 해제
        if self.selected_index is not None and self.selected_key is not None:
            self.set_slot_highlight(self.selected_index, self.selected_key, False)

        # 새 선택 적용
        self.selected_index = index
        self.selected_key = key
        self.set_slot_highlight(index, key, True)

        self.controller.set_selected_slot(index, key)

    def set_slot_highlight(self, index, key, selected):
        # 해당 슬롯의 label 3개 찾아서 스타일 적용
        for i, k, key_lbl, hash_lbl, file_lbl in self.slot_labels:
            if i == index and k == key:
                color = "#add8e6" if selected else "#f0f0f0"
                border = "solid" if selected else "flat"
                key_lbl.configure(bg=color)
                hash_lbl.configure(bg=color)
                file_lbl.configure(bg=color)
                break

    def set_slot_value(self, index, key, value):
        self.component_widgets[index][key].set(value)

    def get_component_values(self):
        return self.component_widgets
    
    def _resize_inner_frame(self, event):
        self.canvas.itemconfig(self.inner_window, width=event.width)