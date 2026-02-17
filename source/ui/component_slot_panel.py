import tkinter as tk


class ComponentSlotPanel(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self._tooltip = None
        self.slot_labels = []
        self.component_widgets = []
        self.selected_index = None
        self.selected_key = None
        self.selected_variant = None

        self.canvas = tk.Canvas(self)
        self.inner_frame = tk.Frame(self.canvas)
        self.scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner_window = self.canvas.create_window(
            (0, 0), window=self.inner_frame, anchor="nw"
        )

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind("<Configure>", self._resize_inner_frame)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _resize_inner_frame(self, event):
        self.canvas.itemconfig(self.inner_window, width=event.width)

    def display_components(self, components, mod_files):
        self.components = components
        self._clear()

        for comp_index, comp in enumerate(components):
            group_frame = self._create_component_group(comp_index, comp)
            group_frame.pack(fill="x", padx=10, pady=5, expand=True)

    def _clear(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.component_widgets.clear()
        self.slot_labels.clear()

    def _create_component_group(self, comp_index, comp):
        group_frame = tk.Frame(self.inner_frame)
        is_group_expanded = tk.BooleanVar(value=True)

        title_label = tk.Label(
            group_frame,
            text=f"▼ {comp['name']}",
            font=("Arial", 10, "bold"),
            anchor="w",
            cursor="hand2",
            bg="#ddd",
            padx=5,
            pady=2,
        )
        title_label.pack(fill="x")

        body_frame = tk.Frame(group_frame)
        body_frame.pack(fill="x", padx=5, pady=2)

        title_label.bind(
            "<Button-1>",
            lambda e: self._toggle_frame(
                is_group_expanded, body_frame, title_label, comp["name"]
            ),
        )

        shared_widgets = {
            key: self._create_slot_row(
                body_frame, comp_index, key, comp["shared"][key], is_variant=False
            )
            for key in comp.get("shared", {})
        }

        variant_widgets = {}
        for label, variant_data in comp.get("variants", {}).items():
            variant_widgets[label] = self._create_variant_block(
                body_frame, comp_index, label, variant_data
            )

        self.component_widgets.append(
            {
                "name": comp["name"],
                "shared": shared_widgets,
                "variants": variant_widgets,
            }
        )

        return group_frame

    def _toggle_frame(self, toggle_var, frame, label, name):
        if toggle_var.get():
            frame.pack_forget()
            toggle_var.set(False)
            label.config(text=f"▶ {name}")
        else:
            frame.pack(fill="x", padx=5, pady=2)
            toggle_var.set(True)
            label.config(text=f"▼ {name}")

    def _create_variant_block(self, parent, comp_index, label, variant_data):
        sub_frame = tk.Frame(parent)
        sub_frame.pack(fill="x", padx=(5, 0), pady=4)

        is_variant_expanded = tk.BooleanVar(value=True)

        var_label = tk.Label(
            sub_frame,
            text=f"▼ {label}",
            font=("Arial", 9, "bold"),
            anchor="w",
            cursor="hand2",
            bg="#eee",
            padx=5,
            pady=1,
        )
        var_label.pack(fill="x")

        content = tk.Frame(sub_frame)
        content.pack(fill="x", padx=(5, 0), pady=2)

        var_label.bind(
            "<Button-1>",
            lambda e: self._toggle_frame(
                is_variant_expanded, content, var_label, label
            ),
        )

        widgets = {
            key: self._create_slot_row(
                content,
                comp_index,
                key,
                variant_data[key],
                is_variant=True,
                variant=label,
            )
            for key in variant_data
        }

        return widgets

    def _create_slot_row(
        self, parent, comp_index, key, hash_value, is_variant=False, variant=None
    ):
        row = tk.Frame(parent)
        row.pack(fill="x", pady=2, expand=True)

        key_label = tk.Label(row, text=key, width=12, anchor="w")
        key_label.grid(row=0, column=0, padx=2, sticky="w")
        key_label.bind(
            "<Button-1>", lambda e: self.select_slot(comp_index, key, variant)
        )

        hash_label = tk.Label(
            row, text=hash_value or "", width=15, anchor="w", bg="#f0f0f0"
        )
        hash_label.grid(row=0, column=1, padx=2, sticky="w")
        hash_label.bind(
            "<Button-1>", lambda e: self.select_slot(comp_index, key, variant)
        )

        val = tk.StringVar(value="")
        file_label = tk.Label(
            row, textvariable=val, anchor="w", bg="#f7f7f7", relief="sunken"
        )
        file_label.grid(row=0, column=2, padx=2, sticky="we")
        file_label.bind(
            "<Button-1>", lambda e: self.select_slot(comp_index, key, variant)
        )

        # 툴팁 바인딩: 레이블에 마우스 올리면 현재 텍스트 표시
        file_label.bind("<Enter>", lambda e, v=val, w=file_label: self._on_label_enter(e, v, w))
        file_label.bind("<Leave>", lambda e: self._on_label_leave(e))
        file_label.bind("<Motion>", lambda e, w=file_label: self._on_label_motion(e, w))

        clear_btn = tk.Button(
            row,
            text="X",
            command=lambda: self.set_slot_value(comp_index, key, "", variant),
            fg="red",
            width=2,
        )
        clear_btn.grid(row=0, column=3, padx=2, sticky="e")

        row.columnconfigure(2, weight=1)
        row.columnconfigure(3, weight=0)

        self.slot_labels.append(
            (comp_index, key, variant, key_label, hash_label, file_label)
        )
        return val

    # ---- tooltip helpers ----
    def _on_label_enter(self, event, var, widget):
        text = var.get()
        if not text:
            return
        self._hide_tooltip()
        try:
            tw = tk.Toplevel(self)
            tw.wm_overrideredirect(True)
            lbl = tk.Label(tw, text=text, bg="#ffffe0", relief="solid", bd=1, justify="left")
            lbl.pack(ipadx=4, ipady=2)
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 20
            tw.wm_geometry(f"+{x}+{y}")
            self._tooltip = tw
        except Exception:
            self._tooltip = None

    def _on_label_leave(self, event=None):
        self._hide_tooltip()

    def _on_label_motion(self, event, widget):
        if not getattr(self, "_tooltip", None):
            return
        try:
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 20
            self._tooltip.wm_geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _hide_tooltip(self):
        if getattr(self, "_tooltip", None):
            try:
                self._tooltip.destroy()
            except Exception:
                pass
            self._tooltip = None

    def select_slot(self, comp_index, key, variant=None):
        if self.selected_index is not None and self.selected_key is not None:
            self.set_slot_highlight(
                self.selected_index, self.selected_key, False, self.selected_variant
            )

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
            self.controller.log(
                f"[비움] {comp_name} ({label}) - {key} 슬롯이 비워졌습니다."
            )

    def get_component_values(self):
        return self.component_widgets

    def _on_mousewheel(self, event):
        try:
            delta = int(event.delta / 120)
            move = -delta
            self.canvas.yview_scroll(move, "units")
        except Exception:
            pass
        return "break"
