"""Общие диалоги: предупреждение, ошибка, подтверждения, справка, переименование."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit,
)

from ..i18n import tr
from ..theme import THEMES, CURRENT_THEME, STYLES


class WarningDialog(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("warning_title"))
        self.setFixedSize(320, 160)
        self.setStyleSheet(f"background-color: {THEMES[CURRENT_THEME]['PANEL_BG']}; {STYLES['TEXT_DARK']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"{STYLES['FONT_BOLD']}; font-size: 12px; border: none; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        btn = QPushButton(tr("ok"))
        btn.setFixedHeight(36)
        btn.setStyleSheet(STYLES["BTN_GRAY"])
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)


class ErrorDialog(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("error_title"))
        self.setFixedSize(320, 160)
        self.setStyleSheet(f"background-color: {THEMES[CURRENT_THEME]['PANEL_BG']}; {STYLES['TEXT_DARK']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"{STYLES['FONT_BOLD']}; font-size: 12px; border: none; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        btn = QPushButton(tr("ok"))
        btn.setFixedHeight(36)
        btn.setStyleSheet(STYLES["BTN_GRAY"])
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)


class ConfirmClearDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("confirm_clear_title"))
        self.setFixedSize(360, 150)
        self.setStyleSheet(f"background-color: {THEMES[CURRENT_THEME]['PANEL_BG']}; {STYLES['TEXT_DARK']}; font-family: Arial;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        lbl = QLabel(tr("confirm_clear_msg"))
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"{STYLES['FONT_BOLD']}; font-size: 12px; border: none; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_yes = QPushButton(tr("yes"))
        self.btn_yes.setFixedHeight(34)
        self.btn_yes.setStyleSheet(STYLES["BTN_GREEN"])
        self.btn_yes.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_yes)

        self.btn_no = QPushButton(tr("no"))
        self.btn_no.setFixedHeight(34)
        self.btn_no.setStyleSheet(STYLES["BTN_GRAY_STATIC"])
        self.btn_no.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_no)

        layout.addLayout(btn_layout)


class ConfirmImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("confirm_import_title"))
        self.setFixedSize(360, 150)
        self.setStyleSheet(f"background-color: {THEMES[CURRENT_THEME]['PANEL_BG']}; {STYLES['TEXT_DARK']}; font-family: Arial;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        lbl = QLabel(tr("confirm_import_msg"))
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"{STYLES['FONT_BOLD']}; font-size: 12px; border: none; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_yes = QPushButton(tr("yes"))
        self.btn_yes.setFixedHeight(34)
        self.btn_yes.setStyleSheet(STYLES["BTN_GREEN"])
        self.btn_yes.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_yes)

        self.btn_no = QPushButton(tr("no"))
        self.btn_no.setFixedHeight(34)
        self.btn_no.setStyleSheet(STYLES["BTN_GRAY_STATIC"])
        self.btn_no.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_no)

        layout.addLayout(btn_layout)


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        t = THEMES[CURRENT_THEME]
        self.setWindowTitle(tr("help_title"))
        self.resize(560, 520)
        self.setMinimumSize(460, 380)
        self.setStyleSheet(f"background-color: {t['PANEL_BG']}; {STYLES['TEXT_DARK']}; font-family: Arial;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setHtml(tr("help_text"))
        self.text_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {t['LOG_BG']};
                color: {t['TEXT_DARK']};
                font-family: Arial;
                font-size: 12px;
                border-radius: 10px;
                border: none;
                padding: 8px;
            }}
        """ + STYLES["SCROLL_BAR"])
        layout.addWidget(self.text_area)

        btn = QPushButton(tr("ok"))
        btn.setFixedHeight(36)
        btn.setStyleSheet(STYLES["BTN_GRAY"])
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)


class RenameDialog(QDialog):
    def __init__(self, current_name, parent=None):
        super().__init__(parent)
        t = THEMES[CURRENT_THEME]
        self.setWindowTitle(tr("rename_title"))
        self.setFixedSize(320, 160)
        self.setStyleSheet(f"background-color: {t['PANEL_BG']}; {STYLES['TEXT_DARK']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl = QLabel(tr("new_name"))
        lbl.setStyleSheet(f"{STYLES['FONT_BOLD']}; font-size: 12px; border: none; background: transparent;")
        layout.addWidget(lbl)

        self.entry = QLineEdit(current_name)
        self.entry.setFixedHeight(32)
        self.entry.setStyleSheet(f"background-color: {t['INPUT_BG']}; color: {t['TEXT_DARK']}; border: 1px solid {t['INPUT_BORDER']}; border-radius: 6px; padding: 5px; font-size: 12px;")
        layout.addWidget(self.entry)

        btn = QPushButton(tr("ok"))
        btn.setFixedHeight(36)
        btn.setStyleSheet(STYLES["BTN_GRAY"])
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def get_name(self):
        return self.entry.text().strip()