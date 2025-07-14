import tkinter as tk
from component_matcher import ComponentMatcherApp
from ui_components import UIComponents
from logger import Logger

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x700")
    root.title("엵툵 컴포넌트 매칭기")

    logger = Logger(root)
    ui = UIComponents(root)
    app = ComponentMatcherApp(root, ui, logger)
    ui.matcher = app
    ui.build_ui()
    logger.attach(root)

    root.mainloop()
