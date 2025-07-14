import tkinter as tk
from component_matcher import ComponentMatcherApp
from ui_components import UIComponents
from logger import Logger

if __name__ == "__main__":
    print("[main.py] 프로그램 시작")
    try:
        root = tk.Tk()
        root.title("Mod Asset Matcher")
        root.geometry("800x600")

        logger = Logger(root)
        ui = UIComponents(root)  # matcher 없이 생성
        app = ComponentMatcherApp(root, ui, logger)
        ui.set_matcher(app)  # 여기서 연결 + UI 빌드

        print("[main.py] mainloop 진입")
        root.mainloop()
        print("[main.py] mainloop 정상 종료")

    except Exception as e:
        import traceback
        print("[main.py] 예외 발생:", e)
        traceback.print_exc()
        input("엔터를 눌러 종료...")