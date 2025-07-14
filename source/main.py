import tkinter as tk
from component_matcher import ComponentMatcherApp
from ui.layout import UIComponents

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x700")
    root.title("엵툵 컴포넌트 매칭기")

    ui = UIComponents(root)
    app = ComponentMatcherApp(root, ui)
    ui.matcher = app

    root.mainloop()