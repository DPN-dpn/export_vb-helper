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

        self.component_widgets = []
        self.slot_labels = []
        self.selected_index = None
        self.selected_key = None
        self.group_contents = []

    def display_components(self, components, mod_files_by_type):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.component_widgets.clear()
        self.slot_labels.clear()
        self.group_contents.clear()

        for idx, comp in enumerate(components):
            outer_frame = tk.Frame(self.inner_frame)
            outer_frame.pack(fill="x", padx=10, pady=5, expand=True)

            is_expanded = tk.BooleanVar(value=True)
            comp_name = comp.get("name", f"컴포넌트 {idx+1}")

            title_label = tk.Label(
                outer_frame,
                text=f"▼ {comp_name}",
                font=("Arial", 10, "bold"),
                anchor="w",
                cursor="hand2",
                bg="#ddd",
                padx=5, pady=2
            )
            title_label.pack(fill="x")

            content_frame = tk.Frame(outer_frame)
            content_frame.pack(fill="x", pady=2)
            self.group_contents.append(content_frame)

            def toggle(e=None, var=is_expanded, frame=content_frame, label=title_label, name=comp_name):
                if var.get():
                    frame.pack_forget()
                    var.set(False)
                    label.config(text=f"▶ {name}")
                else:
                    frame.pack(fill="x", pady=2)
                    var.set(True)
                    label.config(text=f"▼ {name}")

            title_label.bind("<Button-1>", toggle)

            def make_click_handler(i, k):
                return lambda e: self.select_slot(i, k)

            def make_clear_handler(i, k):
                return lambda: self.set_slot_value(i, k, "")

            widget_row = {}

            for key in REQUIRED_COMPONENT_KEYS:
                row = tk.Frame(content_frame)
                row.pack(fill="x", pady=2, expand=True)

                key_label = tk.Label(row, text=key, width=12, anchor="w")
                key_label.grid(row=0, column=0, padx=2, sticky="w")
                key_label.bind("<Button-1>", make_click_handler(idx, key))

                hash_val = comp.get(key) or ""
                hash_label = tk.Label(row, text=hash_val, width=15, anchor="w", bg="#f0f0f0")
                hash_label.grid(row=0, column=1, padx=2, sticky="w")
                hash_label.bind("<Button-1>", make_click_handler(idx, key))

                val = tk.StringVar(value="")
                file_label = tk.Label(row, textvariable=val, anchor="w", bg="#f7f7f7", relief="sunken")
                file_label.grid(row=0, column=2, padx=2, sticky="we")
                file_label.bind("<Button-1>", make_click_handler(idx, key))

                clear_btn = tk.Button(row, text="X", command=make_clear_handler(idx, key), fg="red", width=2)
                clear_btn.grid(row=0, column=3, padx=2, sticky="e")

                row.columnconfigure(2, weight=1)
                row.columnconfigure(3, weight=0)

                self.slot_labels.append((idx, key, key_label, hash_label, file_label))
                widget_row[key] = val

            self.component_widgets.append(widget_row)

    def select_slot(self, index, key):
        if self.selected_index is not None and self.selected_key is not None:
            self.set_slot_highlight(self.selected_index, self.selected_key, False)

        self.selected_index = index
        self.selected_key = key
        self.set_slot_highlight(index, key, True)

        self.controller.set_selected_slot(index, key)
        comp_name = self.controller.matcher.components[index].get("name", f"컴포넌트 {index+1}")
        self.controller.log(f"[선택] {comp_name} - {key} 슬롯 선택됨")

    def set_slot_highlight(self, index, key, selected):
        for i, k, key_lbl, hash_lbl, file_lbl in self.slot_labels:
            if i == index and k == key:
                color = "#add8e6" if selected else "#f0f0f0"
                key_lbl.configure(bg=color)
                hash_lbl.configure(bg=color)
                file_lbl.configure(bg=color)
                break

    def set_slot_value(self, index, key, value):
        self.component_widgets[index][key].set(value)
        comp_name = self.controller.matcher.components[index].get("name", f"컴포넌트 {index+1}")
        if value:
            self.controller.log(f"[할당] {comp_name} - {key} ← {value}")
        else:
            self.controller.log(f"[비움] {comp_name} - {key} 슬롯이 비워졌습니다.")

    def get_component_values(self):
        return self.component_widgets

    def _resize_inner_frame(self, event):
        self.canvas.itemconfig(self.inner_window, width=event.width)