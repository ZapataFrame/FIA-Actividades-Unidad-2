import sys
from PyQt6.QtWidgets import QApplication
from src.app.main_window import MainWindow
import os

def main():
    app = QApplication(sys.argv)

    # Load pastel pink style
    style_path = "src/assets/styles/pink.qss"
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: Style file not found at {style_path}")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
