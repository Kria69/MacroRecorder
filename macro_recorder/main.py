import sys

from PyQt6.QtWidgets import QApplication

from .app import MacroApp


def main():
    app = QApplication(sys.argv)
    window = MacroApp()
    window.show()
    sys.exit(app.exec())