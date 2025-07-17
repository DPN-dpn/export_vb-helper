import tkinter as tk
from ui.layout import MainLayout
from app.matcher import ComponentMatcherApp

def main():
    root = tk.Tk()
    root.title("엵툵 컴포넌트 매칭기")
    root.geometry("1000x700")

    ui = MainLayout(root)
    app = ComponentMatcherApp(ui)
    ui.set_matcher(app)

    root.mainloop()

if __name__ == "__main__":
    main()
