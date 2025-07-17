import tkinter as tk

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

        self.slot_labels = []
        self.selected_index = None
        self.selected_key = None
        self.selected_variant = None
        self.component_widgets = []

    def _resize_inner_frame(self, event):
        self.canvas.itemconfig(self.inner_window, width=event.width)

    def display_components(self, components, mod_files):
        self.components = components

        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        self.component_widgets.clear()
        self.slot_labels.clear()

        for comp_index, comp in enumerate(components):
            group_frame = tk.Frame(self.inner_frame)
            group_frame.pack(fill="x", padx=10, pady=5, expand=True)

            is_group_expanded = tk.BooleanVar(value=True)

            title_label = tk.Label(
                group_frame,
                text=f"▼ {comp['name']}",
                font=("Arial", 10, "bold"),
                anchor="w",
                cursor="hand2",
                bg="#ddd",
                padx=5, pady=2
            )
            title_label.pack(fill="x")

            body_frame = tk.Frame(group_frame)
            body_frame.pack(fill="x", padx=5, pady=2)

            def toggle_group(e=None, var=is_group_expanded, frame=body_frame, label=title_label, name=comp["name"]):
                if var.get():
                    frame.pack_forget()
                    var.set(False)
                    label.config(text=f"▶ {name}")
                else:
                    frame.pack(fill="x", padx=5, pady=2)
                    var.set(True)
                    label.config(text=f"▼ {name}")

            title_label.bind("<Button-1>", toggle_group)

            shared_widgets = {}
            for key in comp.get("shared", {}):
                shared_widgets[key] = self._create_slot_row(body_frame, comp_index, key, comp["shared"][key], is_variant=False)

            variant_widgets = {}
            for label, variant_data in comp.get("variants", {}).items():
                sub_frame = tk.Frame(body_frame)
                sub_frame.pack(fill="x", padx=(5, 0), pady=4)

                is_variant_expanded = tk.BooleanVar(value=True)

                var_label = tk.Label(
                    sub_frame,
                    text=f"▼ {label}",
                    font=("Arial", 9, "bold"),
                    anchor="w",
                    cursor="hand2",
                    bg="#eee",
                    padx=5, pady=1
                )
                var_label.pack(fill="x")

                content = tk.Frame(sub_frame)
                content.pack(fill="x", padx=(5, 0), pady=2)

                def toggle_variant(e=None, var=is_variant_expanded, frame=content, label=var_label, name=label):
                    if var.get():
                        frame.pack_forget()
                        var.set(False)
                        label.config(text=f"▶ {name}")
                    else:
                        frame.pack(fill="x", padx=5, pady=2)
                        var.set(True)
                        label.config(text=f"▼ {name}")

                var_label.bind("<Button-1>", toggle_variant)

                sub_widgets = {}
                for key in variant_data:
                    sub_widgets[key] = self._create_slot_row(content, comp_index, key, variant_data[key], is_variant=True, variant=label)
                variant_widgets[label] = sub_widgets

            self.component_widgets.append({
                "name": comp['name'],
                "shared": shared_widgets,
                "variants": variant_widgets
            })

    def _create_slot_row(self, parent, comp_index, key, hash_value, is_variant=False, variant=None):
        row = tk.Frame(parent)
        row.pack(fill="x", pady=2, expand=True)

        key_label = tk.Label(row, text=key, width=12, anchor="w")
        key_label.grid(row=0, column=0, padx=2, sticky="w")
        key_label.bind("<Button-1>", lambda e: self.select_slot(comp_index, key, variant))

        hash_label = tk.Label(row, text=hash_value or "", width=15, anchor="w", bg="#f0f0f0")
        hash_label.grid(row=0, column=1, padx=2, sticky="w")
        hash_label.bind("<Button-1>", lambda e: self.select_slot(comp_index, key, variant))

        val = tk.StringVar(value="")
        file_label = tk.Label(row, textvariable=val, anchor="w", bg="#f7f7f7", relief="sunken")
        file_label.grid(row=0, column=2, padx=2, sticky="we")
        file_label.bind("<Button-1>", lambda e: self.select_slot(comp_index, key, variant))

        clear_btn = tk.Button(row, text="X", command=lambda: self.set_slot_value(comp_index, key, "", variant), fg="red", width=2)
        clear_btn.grid(row=0, column=3, padx=2, sticky="e")

        row.columnconfigure(2, weight=1)
        row.columnconfigure(3, weight=0)

        self.slot_labels.append((comp_index, key, variant, key_label, hash_label, file_label))
        return val

    def select_slot(self, comp_index, key, variant=None):
        if self.selected_index is not None and self.selected_key is not None:
            self.set_slot_highlight(self.selected_index, self.selected_key, False, self.selected_variant)

        self.selected_index = comp_index
        self.selected_key = key
        self.selected_variant = variant
        self.set_slot_highlight(comp_index, key, True, variant)

        self.controller.set_selected_slot(comp_index, key, variant)

    def set_slot_highlight(self, index, key, selected, variant=None):
        for i, k, v, key_lbl, hash_lbl, file_lbl in self.slot_labels:
            if i == index and k == key and v == variant:
                color = "#add8e6" if selected else "#f0f0f0"
                key_lbl.configure(bg=color)
                hash_lbl.configure(bg=color)
                file_lbl.configure(bg=color)
                break

    def set_slot_value(self, index, key, value, variant=None):
        widget = None
        if variant:
            widget = self.component_widgets[index]["variants"][variant][key]
        else:
            widget = self.component_widgets[index]["shared"][key]

        widget.set(value)
        label = variant if variant else "공통"
        comp_name = self.controller.matcher.components[index]["name"]
        if value:
            self.controller.log(f"[할당] {comp_name} ({label}) - {key} ← {value}")
        else:
            self.controller.log(f"[비움] {comp_name} ({label}) - {key} 슬롯이 비워졌습니다.")

    def get_component_values(self):
        return self.component_widgets
