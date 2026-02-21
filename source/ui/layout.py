import os
import subprocess
import platform
import tkinter as tk
from tkinter import filedialog
import threading

from ui.path_selector import PathSelectorFrame
from ui.component_slot_panel import ComponentSlotPanel
from ui.mod_file_panel import ModFileListPanel
from ui.logger_frame import LoggerFrame

from app import ini_modifier
from app.auto_fill import auto_fill_components
from app.export_to_export_vb import run_export_vb
from config import load_config, save_config


class MainLayout:

    def __init__(self, root: tk.Misc) -> None:
        self.root = root
        self.matcher = None
        self.selected_slot = None
        self.selected_file = None

        # 설정 초기화
        self.config = load_config()
        asset_folder = self.config.get("last_asset_folder")
        mod_folder = self.config.get("last_mod_folder")
        self.last_asset_folder = (
            asset_folder
            if asset_folder and os.path.exists(asset_folder)
            else os.getcwd()
        )
        self.last_mod_folder = (
            mod_folder if mod_folder and os.path.exists(mod_folder) else os.getcwd()
        )

        self.vertical_pane = tk.PanedWindow(root, orient="vertical")
        self.vertical_pane.pack(fill="both", expand=True)

        # 상단 프레임: (왼쪽: 에셋 셀렉터 + 자동 채우기 버튼 + 슬롯 패널, 오른쪽: 모드 셀렉터 + 모드 파일 패널)
        self.content_frame = tk.Frame(self.vertical_pane)
        self.content_frame.pack(fill="both", expand=True)

        # 상단 프레임 좌우 분할
        self.columns_frame = tk.Frame(self.content_frame)
        self.columns_frame.pack(fill="both", expand=True)
        self.columns_frame.grid_rowconfigure(0, weight=1)
        self.columns_frame.grid_columnconfigure(0, weight=1, uniform="cols")
        self.columns_frame.grid_columnconfigure(1, weight=1, uniform="cols")

        # 왼쪽 열: 에셋 선택(위) + 자동 채우기 버튼 + 컴포넌트 슬롯 패널(아래)
        self.left_column = tk.Frame(self.columns_frame)
        self.left_column.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # 에셋 선택
        self.path_selector_asset = PathSelectorFrame(
            self.left_column, self, show_asset=True, show_mod=False
        )
        self.path_selector_asset.pack(side="top", fill="x", padx=5, pady=5)

        # 자동 채우기 버튼
        self.slot_controls = tk.Frame(self.left_column)
        self.slot_controls.pack(side="top", fill="x", padx=5, pady=(0, 5))
        self.auto_fill_btn = tk.Button(
            self.slot_controls, text="자동 채우기", command=self.on_auto_fill
        )
        # 자동 채우기 버튼 숨김
        # self.auto_fill_btn.pack(side="left", expand=True, fill="x", padx=5)

        # 컴포넌트 슬롯 패널
        self.slot_panel = ComponentSlotPanel(self.left_column, self)
        self.slot_panel.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        # 오른쪽 열: 모드 선택(위) + 모드 파일 목록(아래)
        self.right_column = tk.Frame(self.columns_frame)
        self.right_column.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        # 모드 선택
        self.path_selector_mod = PathSelectorFrame(
            self.right_column, self, show_asset=False, show_mod=True
        )
        self.path_selector_mod.pack(side="top", fill="x", padx=5, pady=5)

        # 모드 파일 목록
        self.file_panel = ModFileListPanel(self.right_column, self)
        self.file_panel.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        # 하단 프레임: 내보내기 버튼 + 로그 영역
        self.bottom_frame = tk.Frame(self.vertical_pane)

        # 내보내기 버튼 및 연결 버튼
        self.export_frame = tk.Frame(self.bottom_frame, height=40)
        self.export_frame.pack_propagate(False)

        # 내보내기 버튼 (왼쪽, 넓게)
        self.export_button = tk.Button(self.export_frame, text="내보내기", command=self.export)
        self.export_button.pack(side="left", pady=5, padx=(10, 5), fill="x", expand=True)

        # 작게 오른쪽에 배치할 '엵툵' 버튼
        self.connect_button = tk.Button(self.export_frame, text="엵툵", width=6, command=self.connect_export_vb)
        self.connect_button.pack(side="right", pady=5, padx=(5, 10))

        self.export_frame.pack(side="top", fill="x")

        # 로그 영역
        self.logger = LoggerFrame(self.bottom_frame)
        self.logger.pack(fill="both", expand=True)

        # 상단 하단 프레임 크기 조절 패인
        self.vertical_pane.add(self.content_frame, stretch="always", minsize=220)
        self.vertical_pane.add(self.bottom_frame, minsize=100, stretch="never")

        # 경로 선택 초기화
        if hasattr(self, "path_selector_asset"):
            self.path_selector_asset.asset_path_var.set(self.last_asset_folder)
            if hasattr(self.path_selector_asset, "asset_display_var"):
                self.path_selector_asset.asset_display_var.set(self.last_asset_folder)
            self.path_selector_asset.update_asset_options()
        if hasattr(self, "path_selector_mod"):
            self.path_selector_mod.mod_path_var.set(self.last_mod_folder)
            if hasattr(self.path_selector_mod, "mod_display_var"):
                self.path_selector_mod.mod_display_var.set(self.last_mod_folder)
            self.path_selector_mod.update_mod_options()
        self.path_selector = self

        # 시작 시 config에 저장된 export_vb 경로로 자동 연결 시도
        try:
            evb_path = self.config.get("export_vb_path")
            if evb_path:
                # normalize
                evb_path = os.path.normpath(evb_path)
                self._try_connect_export_vb(evb_path)
        except Exception:
            pass

    def set_matcher(self, matcher):
        self.matcher = matcher
        if not self.matcher:
            return

        # 자산/모드 기본 선택 적용 (콤보박스의 선택 우선, 없으면 마지막 경로 사용)
        self._apply_initial_selection(
            kind="asset",
            selector_attr="path_selector_asset",
            subvar_attr="asset_subvar",
            path_var_attr="asset_path_var",
            last_attr="last_asset_folder",
            matcher_method="select_asset_folder_from_path",
        )

        self._apply_initial_selection(
            kind="mod",
            selector_attr="path_selector_mod",
            subvar_attr="mod_subvar",
            path_var_attr="mod_path_var",
            last_attr="last_mod_folder",
            matcher_method="select_mod_folder_from_path",
        )

    def _apply_initial_selection(
        self,
        kind: str,
        selector_attr: str,
        subvar_attr: str,
        path_var_attr: str,
        last_attr: str,
        matcher_method: str,
    ) -> None:
        ps = getattr(self, selector_attr, None)
        selected = None
        try:
            if ps and hasattr(ps, subvar_attr):
                subname = getattr(ps, subvar_attr).get()
                base = (
                    getattr(self, path_var_attr, None)
                    and getattr(self, path_var_attr).get()
                )
                if base and subname:
                    selected = os.path.join(base, subname)
        except Exception:
            selected = None

        if selected:
            try:
                getattr(self.matcher, matcher_method)(selected)
            except Exception:
                pass
            return

        last = getattr(self, last_attr, None)
        if last:
            try:
                getattr(self.matcher, matcher_method)(last)
            except Exception:
                pass

    def set_selected_slot(self, index, key, variant=None):
        self.selected_slot = (index, key, variant)

    def set_selected_file(self, fname):
        self.selected_file = fname

    def on_auto_fill(self):
        try:
            auto_fill_components(self)
        except Exception as e:
            self.log(f"[오류] 자동 채우기 실패: {e}")

    def assign_selected_file(self):
        if not self.selected_slot or not self.selected_file:
            self.log("[경고] 슬롯 또는 파일이 선택되지 않았습니다.")
            return
        try:
            index, key, variant = self.selected_slot
            self.slot_panel.set_slot_value(index, key, self.selected_file, variant)
        except Exception as e:
            self.log(f"[오류] 슬롯에 파일 할당 중 오류 발생: {e}")

    def connect_export_vb(self):
        """폴더를 선택하고 해당 폴더에 export_vb.py가 있는지 확인하여
        성공 시 로그를 남기고 config에 저장한다.
        """
        try:
            folder = filedialog.askdirectory(title="엵툵 폴더 선택")
            if not folder:
                return

            candidate = os.path.join(folder, "export_vb.py")
            if os.path.isfile(candidate):
                self.log(f"연결 성공: export_vb.py 발견됨 -> {folder}")
                # config에 저장
                try:
                    save_config({"export_vb_path": folder})
                    self.config["export_vb_path"] = folder
                    self.log("설정에 경로 저장 완료")
                    # 연결 성공 시 내보내기 버튼을 엵툵 전용으로 변경
                    try:
                        self.export_button.config(text="엵툵으로 내보내기", command=self.export_to_export_vb)
                        self.log("내보내기 버튼이 '엵툵으로 내보내기'로 변경되었습니다")
                    except Exception:
                        pass
                except Exception as e:
                    self.log(f"설정 저장 실패: {e}")
            else:
                self.log(f"연결 실패: 선택한 폴더에 export_vb.py가 없습니다 -> {folder}")
                self._clear_export_vb_connection()
        except Exception as e:
            self.log(f"export_vb 연결 중 오류: {e}")
            self._clear_export_vb_connection()

    def _try_connect_export_vb(self, folder: str) -> bool:
        """config에 저장된 폴더로 자동 연결 시도 (대화상자 없음).
        성공하면 버튼을 변경하고 config를 정규화하여 저장한다.
        반환: 연결 성공 여부
        """
        try:
            if not folder or not os.path.isdir(folder):
                self.log(f"엵툵 경로 무효: {folder}")
                return False

            candidate = os.path.join(folder, "export_vb.py")
            if os.path.isfile(candidate):
                self.log(f"자동 연결 성공: export_vb.py 발견 -> {folder}")
                # config에 정규화된 경로 저장
                try:
                    save_config({"export_vb_path": os.path.normpath(folder)})
                    self.config["export_vb_path"] = os.path.normpath(folder)
                except Exception:
                    pass

                try:
                    self.export_button.config(text="엵툵으로 내보내기", command=self.export_to_export_vb)
                except Exception:
                    pass
                return True
            else:
                self.log(f"자동 연결 실패: export_vb.py 없음 -> {folder}")
                self._clear_export_vb_connection()
                return False
        except Exception as e:
            self.log(f"자동 연결 중 오류: {e}")
            return False

    def _clear_export_vb_connection(self) -> None:
        """설정에 저장된 export_vb 연결 정보를 제거하고
        내보내기 버튼을 원래대로 복구합니다."""
        try:
            save_config({"export_vb_path": ""})
            self.config["export_vb_path"] = ""
        except Exception:
            pass

        try:
            self.config.pop("export_vb_path", None)
        except Exception:
            pass

        try:
            self.export_button.config(text="내보내기", command=self.export)
        except Exception:
            pass

    def export_to_export_vb(self):
        """엵툵으로 내보내기:
        - 드롭다운에서 선택된 에셋 폴더를 엵툵의 asset(s) 폴더에 같은 이름으로 복사(없으면)
        - 드롭다운에서 선택된 모드 폴더를 엵툵의 mods 폴더에 같은 이름으로 복사(없으면)
        - 복사 완료 후 export_vb.py를 실행하고 출력 로그를 GUI에 표시
        """
        export_root = self.config.get("export_vb_path")
        if not export_root or not os.path.isdir(export_root):
            self.log("엵툵 경로가 설정되어 있지 않거나 존재하지 않습니다. 먼저 연결해 주세요.")
            return

        # export_vb.py 존재 확인; 없으면 설정 제거하고 버튼 복구
        evb_file = os.path.join(export_root, "export_vb.py")
        if not os.path.isfile(evb_file):
            self.log("export_vb.py가 없음 - 연결 설정 제거")
            self._clear_export_vb_connection()
            return

        asset_src = None
        mod_src = None
        try:
            asset_src = self.asset_path_var.get()
        except Exception:
            asset_src = None
        try:
            mod_src = self.mod_path_var.get()
        except Exception:
            mod_src = None

        # 먼저 기존 내보내기(generate_ini)를 실행하여 output에 생성된 폴더를 mods 복사 소스로 사용
        def _task():
            output_root_cfg = self.config.get("output_root", "output")
            # run_export_vb 내부에서 generate_ini를 호출하므로 단순 위임
            try:
                run_export_vb(export_root, asset_src, mod_src, slot_panel=self.slot_panel, output_root_cfg=output_root_cfg, log_callback=self.log)
            except Exception as e:
                self.log(f"엵툵 복사/실행 중 오류: {e}")

        thread = threading.Thread(target=_task, daemon=True)
        thread.start()

    def display_components(self, components, mod_files):
        self.slot_panel.display_components(components, mod_files)
        self.file_panel.set_file_list(mod_files)

    def log(self, msg):
        try:
            self.logger.log(msg)
        except Exception:
            try:
                print(msg)
            except Exception:
                pass

    def on_asset_folder_selected(self, folder):
        if folder:
            self.last_asset_folder = folder
            save_config(
                {"last_asset_folder": folder, "last_mod_folder": self.last_mod_folder}
            )
            if self.matcher:
                self.matcher.select_asset_folder_from_path(folder)

    def on_asset_subfolder_selected(self, subfolder):
        if subfolder and self.matcher:
            self.matcher.select_asset_folder_from_path(subfolder)

    def on_mod_folder_selected(self, folder):
        if folder:
            self.last_mod_folder = folder
            save_config(
                {"last_asset_folder": self.last_asset_folder, "last_mod_folder": folder}
            )
            if self.matcher:
                self.matcher.select_mod_folder_from_path(folder)

    def on_mod_subfolder_selected(self, subfolder):
        if subfolder and self.matcher:
            self.matcher.select_mod_folder_from_path(subfolder)

    def export(self):
        import traceback

        try:
            asset_path = self.asset_path_var.get()
            mod_path = self.mod_path_var.get()
            output_root = self.config.get("output_root", "output")
            output_path = ini_modifier.generate_ini(
                asset_path, mod_path, self.slot_panel, output_root, self.logger
            )
            self.log("내보내기 완료")
            try:
                subprocess.Popen(f'explorer "{output_path}"')
            except Exception as e:
                self.log(f"결과 폴더 열기 실패: {e}")
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            last = tb[-1]
            self.log(
                f"내보내기 실패: {e}\n  File: {last.filename}, line {last.lineno}, in {last.name}\n  Code: {last.line}"
            )
