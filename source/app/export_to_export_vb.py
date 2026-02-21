import os
import shutil
import subprocess
import sys
import platform
from app import ini_modifier


def _log(cb, msg):
    try:
        if cb:
            cb(msg)
        else:
            print(msg)
    except Exception:
        try:
            print(msg)
        except Exception:
            pass


class _LoggerAdapter:
    def __init__(self, cb):
        self._cb = cb

    def log(self, msg):
        _log(self._cb, msg)


def run_export_vb(export_root, asset_src, mod_src, slot_panel=None, output_root_cfg=None, log_callback=None):
    """전체 흐름:
    1) `ini_modifier.generate_ini`를 호출해 기존 내보내기 수행하고 output에 생성된 모드 폴더를 구한다.
    2) asset_src를 export_root의 asset(s) 아래로 복사(없으면).
    3) 모드 소스로 output에서 생성된 폴더를 사용하여 export_root/mods 아래로 복사(없으면).
    4) export_root에서 export_vb.py를 실행하고 로그를 콜백으로 스트리밍.

    slot_panel: generate_ini에 전달할 slot_panel (선택)
    output_root_cfg: generate_ini에 전달할 output_root (선택)
    """
    if not export_root or not os.path.isdir(export_root):
        _log(log_callback, "export_root가 유효하지 않습니다: %s" % export_root)
        return None

    # 1) 기존 내보내기 실행
    output_mod_path = None
    try:
        if output_root_cfg is None:
            output_root_cfg = "output"

        _log(log_callback, "기존 내보내기 실행 중...")

        # generate_ini expects a logger object with .log method
        gen_logger = _LoggerAdapter(log_callback)

        # call generate_ini; if slot_panel provided, use it, otherwise pass None where appropriate
        try:
            output_mod_path = ini_modifier.generate_ini(
                asset_src or "",
                mod_src or "",
                slot_panel,
                output_root_cfg,
                gen_logger,
            )
            _log(log_callback, f"기존 내보내기 완료: {output_mod_path}")
        except Exception as e:
            _log(log_callback, f"기존 내보내기 실패: {e}")
    except Exception as e:
        _log(log_callback, f"내보내기 호출 중 오류: {e}")

    # asset 복사 및 mod 복사 판단
    # asset 폴더 결정
    asset_dest_root = os.path.join(export_root, "asset")
    if not os.path.exists(asset_dest_root):
        alt = os.path.join(export_root, "assets")
        if os.path.exists(alt):
            asset_dest_root = alt

    mods_dest_root = os.path.join(export_root, "mods")

    tasks = []

    if asset_src and os.path.isdir(asset_src):
        dest = os.path.join(asset_dest_root, os.path.basename(os.path.normpath(asset_src)))
        if os.path.exists(dest):
            _log(log_callback, f"asset 존재, 건너뜀: {dest}")
        else:
            tasks.append((asset_src, dest))
    else:
        _log(log_callback, "에셋 폴더 무효, 건너뜀")

    # 모드 소스: output_mod_path 우선, 없으면 전달된 mod_src 사용
    mod_source = output_mod_path if output_mod_path and os.path.isdir(output_mod_path) else mod_src
    if mod_source and os.path.isdir(mod_source):
        dest = os.path.join(mods_dest_root, os.path.basename(os.path.normpath(mod_source)))
        if os.path.exists(dest):
            _log(log_callback, f"mods 존재, 건너뜀: {dest}")
        else:
            tasks.append((mod_source, dest))
    else:
        _log(log_callback, "모드 소스 무효, 건너뜀")

    # 수행
    copied_from_output = None
    copied_dest_paths = []
    # 프로그램의 output root 절대 경로 (안전 삭제 체크용)
    prog_output_root_abs = os.path.abspath(output_root_cfg) if output_root_cfg else None
    for src, dst in tasks:
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copytree(src, dst)
            _log(log_callback, f"복사: {src} -> {dst}")
            copied_dest_paths.append(dst)
            if output_mod_path and os.path.normpath(src) == os.path.normpath(output_mod_path):
                copied_from_output = src
        except Exception as e:
            _log(log_callback, f"복사 실패: {os.path.basename(src)} : {e}")

    # export_vb.py 실행
    try:
        cmd = [sys.executable or "python", "export_vb.py"]
        # Ensure child Python uses UTF-8 for stdout/stderr to avoid
        # UnicodeEncodeError when printing non-encodable chars on Windows.
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PYTHONUTF8", "1")
        proc = subprocess.Popen(
            cmd,
            cwd=export_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            env=env,
        )

        # 스트리밍 출력
        for line in proc.stdout:
            _log(log_callback, line.rstrip())

        proc.wait()
        ret = proc.returncode
        _log(log_callback, f"export_vb.py 종료 (코드: {ret})")

        # 실행이 끝나면 export_vb 폴더의 output 폴더를 탐색기로 연다
        out_dir = os.path.join(export_root, "output")
        if os.path.isdir(out_dir):
            try:
                if platform.system() == "Windows":
                    os.startfile(out_dir)
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", out_dir])
                else:
                    subprocess.Popen(["xdg-open", out_dir])
            except Exception as e:
                _log(log_callback, f"output 열기 실패: {e}")
        else:
            _log(log_callback, f"output 없음: {out_dir}")

        # output에서 복사해온 모드 폴더가 있으면 원본을 삭제
        if copied_from_output:
            try:
                # 안전성 체크: 삭제하려는 경로가 실제로 프로그램의 output 루트 하위인지 확인
                abs_copied = os.path.abspath(copied_from_output)
                if prog_output_root_abs and os.path.commonpath([prog_output_root_abs, abs_copied]) == prog_output_root_abs:
                    try:
                        shutil.rmtree(copied_from_output)
                    except Exception as e:
                        _log(log_callback, f"원본 삭제 실패: {e}")
                else:
                    _log(log_callback, f"원본 삭제 보류: {os.path.basename(copied_from_output)}")
            except Exception as e:
                _log(log_callback, f"원본 output 폴더 삭제 실패: {copied_from_output} : {e}")

        # 이 프로그램이 export_root에 복사해둔 대상(asset/mods)을 삭제
        if copied_dest_paths:
            exp_root_abs = os.path.abspath(export_root)
            for dst in copied_dest_paths:
                try:
                    abs_dst = os.path.abspath(dst)
                    # 안전성 체크: dst가 export_root 하위인지 확인
                    if os.path.commonpath([exp_root_abs, abs_dst]) == exp_root_abs:
                        try:
                            shutil.rmtree(dst)
                        except Exception as e:
                            _log(log_callback, f"복사본 삭제 실패: {e}")
                    else:
                        _log(log_callback, f"복사본 삭제 보류: {os.path.basename(dst)}")
                except Exception as e:
                    _log(log_callback, f"대상 삭제 실패: {dst} : {e}")

        return ret
    except Exception as e:
        _log(log_callback, f"export_vb 실행 중 오류: {e}")
        return None
