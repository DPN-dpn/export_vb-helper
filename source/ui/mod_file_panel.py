import tkinter as tk
from tkinter import ttk
import os


class ModFileListPanel(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.full_file_list = []

        # 필터 입력
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", self.update_filtered_list)
        filter_frame = tk.Frame(self)
        filter_frame.pack(fill="x", padx=2, pady=2)
        tk.Label(filter_frame, text="🔍").pack(side="left", padx=(0, 6))
        tk.Entry(filter_frame, textvariable=self.filter_var).pack(
            side="left", fill="x", expand=True
        )

        # 프레임 구성
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=2, pady=2)

        try:
            style = ttk.Style()
            style.configure("Treeview", rowheight=16)
        except Exception:
            pass

        # 수직 스크롤바 소유자
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")

        # 파일명 목록 (가로 스크롤 포함)
        filename_frame = tk.Frame(tree_frame)
        filename_frame.grid(row=0, column=1, sticky="nsew")
        # 회색 테두리 프레임 안에 흰 배경 라벨 배치
        hdr_frame = tk.Frame(filename_frame, bg="#888888")
        hdr_frame.pack(side="top", fill="x")
        self.filename_hdr_label = tk.Label(
            hdr_frame,
            text="파일명",
            anchor="center",
            justify="center",
            bg="white",
            cursor="hand2",
            relief="flat",
        )
        self.filename_hdr_label.pack(fill="both", expand=True, padx=1, pady=1)
        # 파일명 헤더: 호버/클릭 피드백 + 클릭 시 정렬
        self.filename_hdr_label.bind("<Enter>", self._on_fname_enter)
        self.filename_hdr_label.bind("<Leave>", self._on_fname_leave)
        self.filename_hdr_label.bind("<ButtonPress-1>", self._on_fname_press)
        self.filename_hdr_label.bind("<ButtonRelease-1>", self._on_fname_release)
        self.filename_list = tk.Listbox(filename_frame, exportselection=False)
        fname_hsb = ttk.Scrollbar(filename_frame, orient="horizontal")
        self.filename_list.configure(xscrollcommand=fname_hsb.set)
        fname_hsb.config(command=self.filename_list.xview)
        self.filename_list.pack(fill="both", expand=True, side="top")
        fname_hsb.pack(fill="x", side="bottom")

        # 트리 영역
        tree_area_frame = tk.Frame(tree_frame)
        tree_area_frame.grid(row=0, column=0, sticky="nsew")

        self.tree = ttk.Treeview(
            tree_area_frame, columns=("component", "hash"), show="headings"
        )
        self.tree.heading("component", text="컴포넌트")
        self.tree.heading("hash", text="해시값")
        self.tree.column("component", width=90, minwidth=90, anchor="w", stretch=False)
        self.tree.column("hash", width=90, minwidth=90, anchor="w", stretch=False)
        self.tree.grid(row=0, column=0, sticky="nsew")

        # 헤더 클릭으로 정렬 (component, hash)
        self.tree.heading("component", command=lambda: self._on_heading_click('component'))
        self.tree.heading("hash", command=lambda: self._on_heading_click('hash'))

        # 가로스크롤 공간 맞춤용 여백
        spacer = tk.Frame(tree_area_frame, height=16)
        spacer.grid(row=1, column=0, sticky="ew")
        tree_area_frame.grid_rowconfigure(0, weight=1)
        tree_area_frame.grid_columnconfigure(0, weight=1)

        # 수직 스크롤 연동 (두 위젯)
        def _vsb_cmd(*args):
            try:
                self.tree.yview(*args)
            except Exception:
                pass
            try:
                self.filename_list.yview(*args)
            except Exception:
                pass

        vsb.config(command=_vsb_cmd)
        self.tree.configure(yscrollcommand=vsb.set)
        self.filename_list.configure(yscrollcommand=vsb.set)

        vsb.grid(row=0, column=2, sticky="ns")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(1, weight=1)

        # 이벤트 바인딩
        self.tree.bind("<<TreeviewSelect>>", self.on_file_selected)
        self.tree.bind("<Double-1>", self.on_file_activate)
        self.tree.bind("<Return>", self.on_file_activate)
        self.filename_list.bind("<<ListboxSelect>>", self.on_filename_selected)
        self.filename_list.bind("<Double-Button-1>", self.on_file_activate)
        self.filename_list.bind("<Return>", self.on_file_activate)

        self.tree.bind("<Shift-MouseWheel>", self._on_shift_wheel)
        self.filename_list.bind("<Shift-MouseWheel>", self._on_shift_wheel)

        self.tree.bind("<MouseWheel>", self._on_vertical_mousewheel)
        self.filename_list.bind("<MouseWheel>", self._on_vertical_mousewheel)

        self.tree.bind("<Up>", self._on_vertical_key)
        self.tree.bind("<Down>", self._on_vertical_key)
        self.tree.bind("<Prior>", self._on_vertical_key)
        self.tree.bind("<Next>", self._on_vertical_key)
        self.filename_list.bind("<Up>", self._on_vertical_key)
        self.filename_list.bind("<Down>", self._on_vertical_key)
        self.filename_list.bind("<Prior>", self._on_vertical_key)
        self.filename_list.bind("<Next>", self._on_vertical_key)

        # 행 데이터: (컴포넌트, 해시, 파일명)
        self._rows = []
        # 정렬 상태
        self._sort_column = None
        self._sort_reverse = False

    def set_file_list(self, file_list):
        # None이 들어올 수 있으므로 안전하게 빈 리스트로 대체
        if file_list is None:
            file_list = []
        self.full_file_list = sorted(set(file_list))

        rows = None
        matcher = getattr(self.controller, "matcher", None)
        if matcher and hasattr(matcher, "load_tree_from_mod"):
            try:
                rows = matcher.load_tree_from_mod(self.full_file_list)
            except Exception:
                rows = None

        # rows가 None일 수 있으므로 빈 리스트로 대체
        self._rows = rows if rows is not None else []
        # 기본으로는 현재 정렬 상태를 유지하며 목록 갱신
        self.update_filtered_list()

    def update_filtered_list(self, *args):
        keyword = self.filter_var.get().lower()
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.filename_list.delete(0, tk.END)
        self._displayed_rows = []
        # 정렬 적용
        rows = list(self._rows)
        if self._sort_column:
            key_idx = 0 if self._sort_column == 'component' else (1 if self._sort_column == 'hash' else 2)
            try:
                rows.sort(key=lambda r: (r[key_idx] or '').lower(), reverse=self._sort_reverse)
            except Exception:
                pass

        for orig_idx, (comp, hsh, fname) in enumerate(rows):
            if fname.lower().endswith((".ib", ".buf", ".assets")) and keyword in fname.lower():
                disp_idx = len(self._displayed_rows)
                self._displayed_rows.append((comp, hsh, fname))
                self.tree.insert("", "end", iid=str(disp_idx), values=(comp, hsh))
                self.filename_list.insert(tk.END, fname)

    def _on_heading_click(self, column):
        """헤더 클릭 처리: 클릭한 컬럼을 기준으로 정렬.

        - 처음 클릭 시 내림차순으로 정렬
        - 같은 컬럼을 다시 클릭하면 오름/내림 전환
        컬럼: 'component', 'hash', 'filename'
        """
        # 설정: 처음 클릭이면 내림차순(True)
        if self._sort_column == column:
            # toggle
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = False  # 기본은 오름차순

        # 갱신
        self.update_filtered_list()

    def on_file_selected(self, event):
        sel = None
        try:
            sel = self.tree.selection()
        except Exception:
            sel = None
        if sel:
            try:
                idx = int(sel[0])
                comp, hsh, fname = self._displayed_rows[idx]
            except Exception:
                return
            try:
                self.filename_list.selection_clear(0, tk.END)
                self.filename_list.selection_set(idx)
                self.filename_list.see(idx)
            except Exception:
                pass
            self.controller.set_selected_file(fname)

    def on_filename_selected(self, event):
        sel = self.filename_list.curselection()
        if sel:
            idx = sel[0]
            try:
                comp, hsh, fname = self._displayed_rows[idx]
            except Exception:
                return
            try:
                self.tree.selection_set(str(idx))
                self.tree.see(str(idx))
            except Exception:
                pass
            self.controller.set_selected_file(fname)

    def on_file_activate(self, event):
        sel_tree = self.tree.selection()
        if sel_tree:
            try:
                idx = int(sel_tree[0])
                fname = self._displayed_rows[idx][2]
                self.controller.set_selected_file(fname)
                self.controller.assign_selected_file()
                return
            except Exception:
                pass
        sel_list = self.filename_list.curselection()
        if sel_list:
            try:
                idx = sel_list[0]
                fname = self._displayed_rows[idx][2]
                self.controller.set_selected_file(fname)
                self.controller.assign_selected_file()
            except Exception:
                pass

    # --- helper methods moved from __init__ for readability ---
    def _on_fname_enter(self, event):
        try:
            self.filename_hdr_label.config(bg="#e6e6e6")
        except Exception:
            pass

    def _on_fname_leave(self, event):
        try:
            self.filename_hdr_label.config(bg="white", relief="flat")
        except Exception:
            pass

    def _on_fname_press(self, event):
        try:
            self.filename_hdr_label.config(relief="sunken")
        except Exception:
            pass

    def _on_fname_release(self, event):
        try:
            self.filename_hdr_label.config(relief="flat")
        except Exception:
            pass
        self._on_heading_click('filename')

    def _vsb_cmd(self, *args):
        try:
            self.tree.yview(*args)
        except Exception:
            pass
        try:
            self.filename_list.yview(*args)
        except Exception:
            pass

    def _on_shift_wheel(self, event):
        try:
            delta = int(event.delta / 120)
            self.filename_list.xview_scroll(-delta, "units")
        except Exception:
            pass

    def _on_vertical_mousewheel(self, event):
        try:
            delta = int(event.delta / 120)
            move = -delta
            self.tree.yview_scroll(move, "units")
            self.filename_list.yview_scroll(move, "units")
        except Exception:
            pass
        return "break"

    def _on_vertical_key(self, event):
        ks = event.keysym
        # Up/Down: move selection in displayed list
        if ks in ("Up", "Down"):
            count = len(self._displayed_rows) if hasattr(self, '_displayed_rows') else 0
            if count == 0:
                return "break"

            # determine current index from tree selection or listbox
            cur_idx = None
            try:
                sel = self.tree.selection()
                if sel:
                    cur_idx = int(sel[0])
            except Exception:
                cur_idx = None

            if cur_idx is None:
                try:
                    lsel = self.filename_list.curselection()
                    if lsel:
                        cur_idx = int(lsel[0])
                except Exception:
                    cur_idx = None

            if cur_idx is None:
                # if no selection, start at end for Up, start for Down
                cur_idx = count - 1 if ks == 'Up' else 0
            else:
                cur_idx = max(0, min(count - 1, cur_idx + (-1 if ks == 'Up' else 1)))

            # apply selection and ensure visible
            try:
                self.tree.selection_set(str(cur_idx))
                self.tree.see(str(cur_idx))
            except Exception:
                pass
            try:
                self.filename_list.selection_clear(0, tk.END)
                self.filename_list.selection_set(cur_idx)
                self.filename_list.see(cur_idx)
            except Exception:
                pass

            try:
                comp, hsh, fname = self._displayed_rows[cur_idx]
                self.controller.set_selected_file(fname)
            except Exception:
                pass

            return "break"

        # Page up/down: scroll pages
        if ks == "Prior":
            self.tree.yview_scroll(-1, "pages")
            self.filename_list.yview_scroll(-1, "pages")
            return "break"
        if ks == "Next":
            self.tree.yview_scroll(1, "pages")
            self.filename_list.yview_scroll(1, "pages")
            return "break"
