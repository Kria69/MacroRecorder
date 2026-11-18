"""Палитры тем и генератор QSS-стилей."""

CURRENT_THEME = "light"

THEMES = {
    "light": {
        "MAIN_BG": "#F4F6F9",
        "PANEL_BG": "#FFFFFF",
        "TEXT_DARK": "#2C3E50",
        "BTN_GRAY_BG": "#BDC3C7",
        "BTN_GRAY_TEXT": "#2C3E50",
        "BTN_GRAY_HOVER_BG": "#27AE60",
        "BTN_GRAY_HOVER_TEXT": "#FFFFFF",
        "BTN_GRAY_PRESSED_BG": "#219A52",
        "BTN_STATIC_HOVER_BG": "#CFD8DC",
        "BTN_STATIC_PRESSED_BG": "#AAB7C4",
        "GREEN": "#27AE60",
        "GREEN_HOVER": "#2ECC71",
        "RED": "#E74C3C",
        "RED_HOVER": "#C0392B",
        "DARK_BTN_BG": "#34495E",
        "DARK_BTN_HOVER": "#2C3E50",
        "SCROLL_BG": "#F1F5F9",
        "SCROLL_HANDLE": "#CBD5E1",
        "SCROLL_HANDLE_HOVER": "#94A3B8",
        "MENU_BORDER": "#BDC3C7",
        "LOG_BG": "#F8F9FA",
        "PROFILE_BG": "#ECF0F1",
        "TOOLTIP_BG": "#34495E",
        "HK_BTN_BG": "#334155",
        "ROW_BG": "#F8FAFC",
        "ROW_BORDER": "#E2E8F0",
        "ROW_TEXT": "#1E293B",
        "RESET_BG": "#64748B",
        "INPUT_BG": "#F8FAFC",
        "INPUT_BORDER": "#CBD5E1",
    },
    "dark": {
        "MAIN_BG": "#1E293B",
        "PANEL_BG": "#273449",
        "TEXT_DARK": "#E2E8F0",
        "BTN_GRAY_BG": "#475569",
        "BTN_GRAY_TEXT": "#E2E8F0",
        "BTN_GRAY_HOVER_BG": "#27AE60",
        "BTN_GRAY_HOVER_TEXT": "#FFFFFF",
        "BTN_GRAY_PRESSED_BG": "#219A52",
        "BTN_STATIC_HOVER_BG": "#526075",
        "BTN_STATIC_PRESSED_BG": "#3B4759",
        "GREEN": "#27AE60",
        "GREEN_HOVER": "#2ECC71",
        "RED": "#E74C3C",
        "RED_HOVER": "#C0392B",
        "DARK_BTN_BG": "#0F172A",
        "DARK_BTN_HOVER": "#1E293B",
        "SCROLL_BG": "#1E293B",
        "SCROLL_HANDLE": "#475569",
        "SCROLL_HANDLE_HOVER": "#64748B",
        "MENU_BORDER": "#475569",
        "LOG_BG": "#0F172A",
        "PROFILE_BG": "#334155",
        "TOOLTIP_BG": "#0F172A",
        "HK_BTN_BG": "#0F172A",
        "ROW_BG": "#334155",
        "ROW_BORDER": "#475569",
        "ROW_TEXT": "#E2E8F0",
        "RESET_BG": "#475569",
        "INPUT_BG": "#334155",
        "INPUT_BORDER": "#475569",
    },
}


def build_styles():
    """Генерирует словарь стилей на основе текущей темы."""
    t = THEMES[CURRENT_THEME]
    return {
        "MAIN_BG": f"background-color: {t['MAIN_BG']};",
        "WHITE_PANEL": f"background-color: {t['PANEL_BG']}; border-radius: 15px;",
        "TEXT_DARK": f"color: {t['TEXT_DARK']};",
        "FONT_BOLD": "font-weight: bold;",
        "BTN_GRAY": f"""
            QPushButton {{ 
                background-color: {t['BTN_GRAY_BG']}; 
                color: {t['BTN_GRAY_TEXT']}; 
                border-radius: 8px; 
                font-weight: bold; 
                border: none; 
            }}
            QPushButton:hover {{ 
                background-color: {t['BTN_GRAY_HOVER_BG']}; 
                color: {t['BTN_GRAY_HOVER_TEXT']}; 
            }}
            QPushButton:pressed {{
                background-color: {t['BTN_GRAY_PRESSED_BG']};
            }}
        """,
        "BTN_GRAY_STATIC": f"""
            QPushButton {{ 
                background-color: {t['BTN_GRAY_BG']}; 
                color: {t['BTN_GRAY_TEXT']}; 
                border-radius: 8px; 
                font-weight: bold; 
                border: none; 
            }}
            QPushButton:hover {{ 
                background-color: {t['BTN_STATIC_HOVER_BG']}; 
                color: {t['BTN_GRAY_TEXT']}; 
            }}
            QPushButton:pressed {{
                background-color: {t['BTN_STATIC_PRESSED_BG']};
                color: {t['BTN_GRAY_TEXT']};
            }}
        """,
        "BTN_GREEN": f"""
            QPushButton {{ background-color: {t['GREEN']}; color: white; border-radius: 10px; font-weight: bold; border: none; }}
            QPushButton:hover {{ background-color: {t['GREEN_HOVER']}; }}
        """,
        "BTN_RED": f"""
            QPushButton {{ background-color: {t['RED']}; color: white; border-radius: 10px; font-weight: bold; border: none; }}
            QPushButton:hover {{ background-color: {t['RED_HOVER']}; }}
        """,
        "BTN_DARK": f"""
            QPushButton {{ background-color: {t['DARK_BTN_BG']}; color: white; border-radius: 10px; font-weight: bold; border: none; }}
            QPushButton:hover {{ background-color: {t['DARK_BTN_HOVER']}; }}
        """,
        "SCROLL_BAR": f"""
            QScrollBar:vertical {{ background: {t['SCROLL_BG']}; width: 10px; margin: 0px; border-radius: 5px; }}
            QScrollBar::handle:vertical {{ background: {t['SCROLL_HANDLE']}; min-height: 20px; border-radius: 5px; }}
            QScrollBar::handle:vertical:hover {{ background: {t['SCROLL_HANDLE_HOVER']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """,
        "MENU": f"""
            QMenu {{ background-color: {t['PANEL_BG']}; color: {t['TEXT_DARK']}; border-radius: 10px; border: 1px solid {t['MENU_BORDER']}; padding: 5px; }}
            QMenu::item {{ padding: 6px 20px; border-radius: 6px; }}
            QMenu::item:selected {{ background-color: {t['GREEN']}; color: white; }}
        """,
        "LOG_AREA": f"""
            QTextEdit {{ background-color: {t['LOG_BG']}; color: {t['TEXT_DARK']}; font-family: Consolas; font-size: 11px; border-radius: 10px; border: none; }}
        """,
    }


STYLES = build_styles()