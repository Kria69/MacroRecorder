"""Панель администратора: статус прав, перезапуск с повышением, debug mode, логи, информация."""

import os
import sys
import ctypes
import glob

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QFrame, QCheckBox,
    QGridLayout, QTextEdit,
)

from ..i18n import tr
from ..theme import THEMES, CURRENT_THEME, STYLES
from .. import layout_utils
from .common import ConfirmClearDialog


def is_admin():
    """Проверяет, запущен ли процесс с правами администратора."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def restart_as_admin():
    """
    Перезапускает текущий скрипт с запросом повышения прав (UAC).
    Возвращает True, если ShellExecuteW принял запрос, False при ошибке/отказе.
    """
    try:
        exe = sys.executable
        if os.path.basename(exe).lower().startswith("pythonw"):
            exe = os.path.join(os.path.dirname(exe), "python.exe")

        params = " ".join([f'"{a}"' for a in sys.argv])

        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe, params, None, 1
        )
        return ret > 32
    except Exception:
        return False


class LogsDialog(QDialog):
    """Окно просмотра всех логов из папки logs."""
    
    def __init__(self, log_dir, parent=None):
        super().__init__(parent)
        t = THEMES[CURRENT_THEME]
        self.setWindowTitle(tr("admin_logs_title"))
        self.resize(700, 500)
        self.setMinimumSize(500, 350)
        self.setStyleSheet(f"background-color: {t['PANEL_BG']}; {STYLES['TEXT_DARK']}; font-family: Arial;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {t['LOG_BG']};
                color: {t['TEXT_DARK']};
                font-family: Consolas, monospace;
                font-size: 11px;
                border-radius: 8px;
                border: 1px solid {t['ROW_BORDER']};
                padding: 8px;
            }}
        """ + STYLES["SCROLL_BAR"])
        
        log_content = self._load_logs(log_dir)
        self.text_area.setPlainText(log_content)
        
        layout.addWidget(self.text_area)
        
        btn_close = QPushButton(tr("ok"))
        btn_close.setFixedHeight(36)
        btn_close.setStyleSheet(STYLES["BTN_GRAY"])
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
    
    def _load_logs(self, log_dir):
        """Читает все .log файлы из директории и объединяет их."""
        if not os.path.isdir(log_dir):
            return f"[{tr('admin_logs_title')}] Directory not found: {log_dir}"
        
        log_files = sorted(glob.glob(os.path.join(log_dir, "*.log")), reverse=True)
        
        if not log_files:
            return f"[{tr('admin_logs_title')}] No log files found in {log_dir}"
        
        parts = []
        for filepath in log_files:
            filename = os.path.basename(filepath)
            parts.append(f"===== {filename} =====")
            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                parts.append(content if content.strip() else "(empty)")
            except Exception as e:
                parts.append(f"[Error reading file: {e}]")
            parts.append("")
        
        return "\n".join(parts)


class ConfirmClearLogsDialog(QDialog):
    """Диалог подтверждения очистки логов."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        t = THEMES[CURRENT_THEME]
        self.setWindowTitle(tr("confirm_clear_logs_title"))
        self.setFixedSize(380, 150)
        self.setStyleSheet(f"background-color: {t['PANEL_BG']}; {STYLES['TEXT_DARK']}; font-family: Arial;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        lbl = QLabel(tr("confirm_clear_logs_msg"))
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"{STYLES['FONT_BOLD']}; font-size: 12px; border: none; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.btn_yes = QPushButton(tr("yes"))
        self.btn_yes.setFixedHeight(34)
        self.btn_yes.setStyleSheet(STYLES["BTN_RED"])
        self.btn_yes.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_yes)
        
        self.btn_no = QPushButton(tr("no"))
        self.btn_no.setFixedHeight(34)
        self.btn_no.setStyleSheet(STYLES["BTN_GRAY_STATIC"])
        self.btn_no.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_no)
        
        layout.addLayout(btn_layout)


class AdminPanelDialog(QDialog):
    def __init__(self, parent=None, data_dir="", hotkeys=None, debug_mode=False, on_debug_changed=None):
        super().__init__(parent)
        t = THEMES[CURRENT_THEME]
        self.setWindowTitle(tr("admin_title"))
        self.resize(480, 460)
        self.setMinimumSize(400, 400)
        self.setStyleSheet(f"background-color: {t['PANEL_BG']}; {STYLES['TEXT_DARK']}; font-family: Arial;")

        self._data_dir = data_dir
        self._hotkeys = hotkeys or {}
        self._restart_requested = False
        self._on_debug_changed = on_debug_changed
        self._log_dir = os.path.join(data_dir, "logs") if data_dir else ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # --- Статус прав ---
        status_row = QWidget()
        status_layout = QHBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)

        lbl_status_title = QLabel(tr("admin_status"))
        lbl_status_title.setStyleSheet(f"{STYLES['FONT_BOLD']} font-size: 13px; background: transparent;")
        status_layout.addWidget(lbl_status_title)

        self.lbl_status_value = QLabel()
        self.lbl_status_value.setStyleSheet("font-size: 13px; font-weight: bold; background: transparent;")
        status_layout.addWidget(self.lbl_status_value)
        status_layout.addStretch()

        layout.addWidget(status_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {t['ROW_BORDER']}; border: none;")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # --- Кнопка перезапуска (одна в строке) ---
        self.btn_restart = QPushButton(tr("admin_restart"))
        self.btn_restart.setFixedHeight(38)
        self.btn_restart.setStyleSheet(STYLES["BTN_GREEN"])
        self.btn_restart.clicked.connect(self._on_restart_clicked)
        layout.addWidget(self.btn_restart)

        lbl_hint = QLabel(tr("admin_restart_hint"))
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet(f"font-size: 11px; color: {t['ROW_TEXT']}; background: transparent;")
        layout.addWidget(lbl_hint)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background-color: {t['ROW_BORDER']}; border: none;")
        sep2.setFixedHeight(1)
        layout.addWidget(sep2)

        # --- Debug Mode ---
        debug_row = QWidget()
        debug_layout = QVBoxLayout(debug_row)
        debug_layout.setContentsMargins(0, 0, 0, 0)
        debug_layout.setSpacing(4)

        self.chk_debug = QCheckBox(tr("admin_debug_mode"))
        self.chk_debug.setChecked(debug_mode)
        self.chk_debug.setStyleSheet(f"""
            QCheckBox {{
                font-size: 12px;
                font-weight: bold;
                color: {t['TEXT_DARK']};
                background: transparent;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {t['BTN_GRAY_BG']};
                border-radius: 4px;
                background: {t['PANEL_BG']};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {t['GREEN_HOVER']};
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {t['GREEN']};
                background: {t['GREEN']};
            }}
            QCheckBox::indicator:checked:hover {{
                border: 2px solid {t['GREEN_HOVER']};
                background: {t['GREEN_HOVER']};
            }}
        """)
        self.chk_debug.toggled.connect(self._on_debug_toggled)
        debug_layout.addWidget(self.chk_debug)

        lbl_debug_hint = QLabel(tr("admin_debug_hint"))
        lbl_debug_hint.setWordWrap(True)
        lbl_debug_hint.setStyleSheet(f"font-size: 11px; color: {t['ROW_TEXT']}; background: transparent;")
        debug_layout.addWidget(lbl_debug_hint)

        layout.addWidget(debug_row)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet(f"background-color: {t['ROW_BORDER']}; border: none;")
        sep3.setFixedHeight(1)
        layout.addWidget(sep3)

        # --- Информация: хоткеи (2 столбца x 5 строк) + раскладка ---
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        lbl_hk_title = QLabel(tr("admin_hotkeys"))
        lbl_hk_title.setStyleSheet(f"{STYLES['FONT_BOLD']} font-size: 11px; background: transparent;")
        info_layout.addWidget(lbl_hk_title)

        hk_grid = QGridLayout()
        hk_grid.setSpacing(4)
        hk_grid.setHorizontalSpacing(12)

        sorted_hk = sorted(self._hotkeys.items())
        for idx, (k, v) in enumerate(sorted_hk):
            row = idx // 2
            col = idx % 2
            cell = QWidget()
            cell_layout = QHBoxLayout(cell)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(4)

            lbl_key = QLabel(f"{k}:")
            lbl_key.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {t['ROW_TEXT']}; background: transparent;")
            cell_layout.addWidget(lbl_key)

            lbl_val = QLabel(v.upper())
            lbl_val.setStyleSheet(f"font-size: 10px; color: {t['TEXT_DARK']}; background: transparent;")
            cell_layout.addWidget(lbl_val)
            cell_layout.addStretch()

            hk_grid.addWidget(cell, row, col)

        info_layout.addLayout(hk_grid)

        sep4 = QFrame()
        sep4.setFrameShape(QFrame.Shape.HLine)
        sep4.setStyleSheet(f"background-color: {t['ROW_BORDER']}; border: none;")
        sep4.setFixedHeight(1)
        info_layout.addWidget(sep4)

        layout_row = QWidget()
        layout_row_layout = QHBoxLayout(layout_row)
        layout_row_layout.setContentsMargins(0, 0, 0, 0)
        layout_row_layout.setSpacing(6)

        lbl_layout_title = QLabel(tr("admin_layout"))
        lbl_layout_title.setStyleSheet(f"{STYLES['FONT_BOLD']} font-size: 11px; background: transparent;")
        layout_row_layout.addWidget(lbl_layout_title)

        self.lbl_layout_value = QLabel("?")
        self.lbl_layout_value.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {t['GREEN']}; background: transparent;")
        layout_row_layout.addWidget(self.lbl_layout_value)
        layout_row_layout.addStretch()

        info_layout.addWidget(layout_row)

        layout.addLayout(info_layout)
        layout.addStretch()

        # --- Нижние кнопки: Логи + Очистить логи ---
        bottom_buttons_row = QWidget()
        bottom_buttons_layout = QHBoxLayout(bottom_buttons_row)
        bottom_buttons_layout.setContentsMargins(0, 0, 0, 0)
        bottom_buttons_layout.setSpacing(10)

        self.btn_logs = QPushButton(tr("admin_logs_btn"))
        self.btn_logs.setFixedHeight(36)
        self.btn_logs.setStyleSheet(STYLES["BTN_DARK"])
        self.btn_logs.clicked.connect(self._on_logs_clicked)
        bottom_buttons_layout.addWidget(self.btn_logs)

        self.btn_clear_logs = QPushButton(tr("admin_clear_logs_btn"))
        self.btn_clear_logs.setFixedHeight(36)
        self.btn_clear_logs.setStyleSheet(STYLES["BTN_RED"])
        self.btn_clear_logs.clicked.connect(self._on_clear_logs_clicked)
        bottom_buttons_layout.addWidget(self.btn_clear_logs)

        layout.addWidget(bottom_buttons_row)

        # --- Кнопка закрытия ---
        btn_close = QPushButton(tr("ok"))
        btn_close.setFixedHeight(36)
        btn_close.setStyleSheet(STYLES["BTN_GRAY"])
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self._update_status_display()
        self._update_layout_display()

        self._layout_timer = QTimer(self)
        self._layout_timer.timeout.connect(self._update_layout_display)
        self._layout_timer.start(200)

    def _update_layout_display(self):
        try:
            hkl = layout_utils.get_current_layout_hkl()
            name = layout_utils.layout_name(hkl)
            self.lbl_layout_value.setText(name)
        except Exception:
            self.lbl_layout_value.setText("?")

    def _update_status_display(self):
        t = THEMES[CURRENT_THEME]
        if is_admin():
            self.lbl_status_value.setText(tr("admin_is_admin"))
            self.lbl_status_value.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {t['GREEN']}; background: transparent;")
            self.btn_restart.setEnabled(False)
            self.btn_restart.setStyleSheet(STYLES["BTN_GRAY_STATIC"])
        else:
            self.lbl_status_value.setText(tr("admin_is_user"))
            self.lbl_status_value.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {t['RED']}; background: transparent;")
            self.btn_restart.setEnabled(True)
            self.btn_restart.setStyleSheet(STYLES["BTN_GREEN"])

    def _on_restart_clicked(self):
        if is_admin():
            self.accept()
            return

        ok = restart_as_admin()
        if ok:
            self._restart_requested = True
            self.accept()
        else:
            self.setWindowTitle(tr("admin_uac_denied"))

    def _on_logs_clicked(self):
        dlg = LogsDialog(self._log_dir, self)
        dlg.exec()

    def _on_clear_logs_clicked(self):
        dlg = ConfirmClearLogsDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        
        if not os.path.isdir(self._log_dir):
            return
        
        deleted = 0
        for filepath in glob.glob(os.path.join(self._log_dir, "*.log")):
            try:
                os.remove(filepath)
                deleted += 1
            except Exception:
                pass
        
        # Обновляем текст в окне логов, если оно открыто (не реализовано здесь,
        # так как LogsDialog модальный и закрывается перед очисткой)

    def _on_debug_toggled(self, checked):
        if self._on_debug_changed:
            self._on_debug_changed(checked)

    def restart_requested(self):
        return self._restart_requested