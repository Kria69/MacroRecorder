"""Работа с раскладкой клавиатуры через WinAPI."""

import ctypes
from ctypes import wintypes
import winreg
import time

from .i18n import tr


def get_current_layout_hkl():
    """Возвращает раскладку активного окна или текущего потока."""
    active = get_focus_layout_hkl() or get_foreground_layout_hkl()
    if active:
        return active
    return ctypes.windll.user32.GetKeyboardLayout(0)


def get_foreground_layout_hkl():
    """Раскладка активного окна."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if hwnd:
            tid = user32.GetWindowThreadProcessId(hwnd, None)
            if tid:
                hkl = user32.GetKeyboardLayout(tid)
                if hkl:
                    return hkl
    except Exception:
        pass
    return None


def get_focus_layout_hkl():
    """Раскладка потока с фокусом ввода (GetGUIThreadInfo)."""
    try:
        user32 = ctypes.windll.user32

        class RECT(ctypes.Structure):
            _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                        ("right", wintypes.LONG), ("bottom", wintypes.LONG)]

        class GUITHREADINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD),
                        ("flags", wintypes.DWORD),
                        ("hwndActive", wintypes.HWND),
                        ("hwndFocus", wintypes.HWND),
                        ("hwndCapture", wintypes.HWND),
                        ("hwndMenuOwner", wintypes.HWND),
                        ("hwndMoveSize", wintypes.HWND),
                        ("hwndCaret", wintypes.HWND),
                        ("rcCaret", RECT)]

        info = GUITHREADINFO()
        info.cbSize = ctypes.sizeof(GUITHREADINFO)
        if user32.GetGUIThreadInfo(0, ctypes.byref(info)):
            hwnd = info.hwndFocus or info.hwndActive
            if hwnd:
                tid = user32.GetWindowThreadProcessId(hwnd, None)
                if tid:
                    hkl = user32.GetKeyboardLayout(tid)
                    if hkl:
                        return hkl
    except Exception:
        pass
    return None


def refresh_input_state():
    """Принудительно обновляет кэш раскладки."""
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return
        fg_tid = user32.GetWindowThreadProcessId(hwnd, None)
        my_tid = kernel32.GetCurrentThreadId()
        if fg_tid and fg_tid != my_tid:
            if user32.AttachThreadInput(my_tid, fg_tid, True):
                user32.GetKeyboardLayout(fg_tid)
                user32.AttachThreadInput(my_tid, fg_tid, False)
    except Exception:
        pass


def layouts_match(hkl1, hkl2):
    """Сравнивает раскладки по LANGID."""
    if hkl1 is None or hkl2 is None:
        return False
    if hkl1 == hkl2:
        return True
    return (int(hkl1) & 0xFFFF) == (int(hkl2) & 0xFFFF)


def layout_name(hkl):
    """Человекочитаемое название раскладки."""
    if hkl is None:
        return "?"
    try:
        langid = int(hkl) & 0xFFFF
        lang_codes = {
            0x0409: "US", 0x0809: "GB", 0x0419: "RU", 0x0422: "UA",
            0x0423: "BY", 0x0407: "DE", 0x040C: "FR", 0x0410: "IT",
            0x0C0A: "ES", 0x0415: "PL", 0x0405: "CZ", 0x041F: "TR",
            0x0411: "JP", 0x0412: "KR", 0x0804: "CN", 0x0404: "TW",
            0x0408: "GR", 0x040D: "IL", 0x0401: "SA", 0x0429: "IR",
            0x043F: "KZ", 0x0440: "KG", 0x0443: "UZ", 0x0444: "TT",
            0x042B: "AM", 0x0437: "GE", 0x042C: "AZ", 0x0416: "BR",
            0x0816: "PT", 0x0413: "NL", 0x041D: "SE", 0x040B: "FI",
            0x0406: "DK", 0x0414: "NO", 0x040E: "HU", 0x0418: "RO",
            0x041A: "HR", 0x0424: "SI", 0x041B: "SK", 0x0402: "BG",
            0x0425: "EE", 0x0426: "LV", 0x0427: "LT", 0x042A: "VN",
            0x041E: "TH", 0x0439: "IN",
        }
        code = lang_codes.get(langid)
        if code is None:
            code = f"0x{langid:04X}"
        return f"{code} {tr('layout_suffix')}"
    except Exception:
        return str(hkl)


def is_target_layout_active(target_hkl):
    """Проверяет раскладку именно активного окна, а не потока Macro Recorder."""
    if target_hkl is None:
        return False
    refresh_input_state()
    focus = get_focus_layout_hkl()
    foreground = get_foreground_layout_hkl()
    # Не используем GetKeyboardLayout(0): он возвращает раскладку потока
    # приложения-рекордера и создавал ложное сообщение о синхронизации.
    return any(
        layout is not None and layouts_match(layout, target_hkl)
        for layout in (focus, foreground)
    )


def release_stuck_modifiers():
    """Отпускает залипшие модификаторы."""
    user32 = ctypes.windll.user32
    VK_KEYUP = 0x0002
    modifier_vks = [0x10, 0x11, 0x12, 0x5B, 0x5C, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5]
    for vk in modifier_vks:
        try:
            if user32.GetAsyncKeyState(vk) & 0x8000:
                user32.keybd_event(vk, 0, VK_KEYUP, 0)
        except Exception:
            pass
    time.sleep(0.05)


def detect_system_language_hotkey(logger):
    """Читает системную комбинацию переключения языка из реестра."""
    try:
        key_path = r"Control Panel\Input Method\Hot Keys"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            idx = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, idx)
                    subkey = winreg.OpenKey(key, subkey_name)
                    value, reg_type = winreg.QueryValueEx(subkey, "1")
                    winreg.CloseKey(subkey)

                    modifiers = int.from_bytes(value[4:8], byteorder='little')
                    virtual_key = int.from_bytes(value[8:12], byteorder='little')
                    target_ime = int.from_bytes(value[0:4], byteorder='little')

                    if target_ime == 0x00000001 and virtual_key != 0:
                        parts = []
                        if modifiers & 0x0008: parts.append('win')
                        if modifiers & 0x0002: parts.append('ctrl')
                        if modifiers & 0x0001: parts.append('alt')
                        if modifiers & 0x0004: parts.append('shift')

                        vk_names = {0x20: 'space', 0x14: 'caps'}
                        if virtual_key in vk_names:
                            parts.append(vk_names[virtual_key])

                        combo = '+'.join(parts)
                        if combo:
                            logger.debug(f"[LAYOUT] Detected system lang hotkey: {combo}")
                            return combo

                    idx += 1
                except OSError:
                    break
    except Exception as e:
        logger.warning(f"Failed to detect system lang hotkey from registry: {e}")

    # На Windows 10/11 по умолчанию переключение часто назначено на Win+Space.
    return "win+space"


def activate_layout(target_hkl, logger):
    """Назначает целевую раскладку активному окну напрямую через WinAPI."""
    if target_hkl is None:
        return False
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        # WM_INPUTLANGCHANGEREQUEST надёжнее переключения Alt+Shift/Win+Space:
        # он выбирает конкретную HKL, а не переключает раскладки вслепую.
        WM_INPUTLANGCHANGEREQUEST = 0x0050
        result = user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, int(target_hkl))
        logger.debug(f"[LAYOUT] WM_INPUTLANGCHANGEREQUEST sent to hwnd={hwnd}, result={result}")
        return bool(result)
    except Exception as exc:
        logger.warning(f"[LAYOUT] Direct layout activation failed: {exc}")
        return False


def ensure_layout(target_hkl, system_lang_switch_combo, logger, attempts=4):
    """Выбирает записанную раскладку и проверяет результат после каждой попытки."""
    if target_hkl is None:
        return False
    combo = system_lang_switch_combo or "win+space"
    for attempt in range(attempts):
        refresh_input_state()
        if is_target_layout_active(target_hkl):
            logger.debug(f"[LAYOUT] Target layout is active: {layout_name(target_hkl)}")
            return True
        logger.debug(f"[LAYOUT] Layout mismatch (attempt {attempt + 1}/{attempts})")
        activate_layout(target_hkl, logger)
        time.sleep(0.25)
        refresh_input_state()
        if is_target_layout_active(target_hkl):
            return True
        # Fallback для приложений, которые игнорируют WM_INPUTLANGCHANGEREQUEST.
        if send_lang_switch_once(combo, logger):
            time.sleep(0.25)
    refresh_input_state()
    result = is_target_layout_active(target_hkl)
    logger.debug(f"[LAYOUT] Final layout check: {result}")
    return result


def send_lang_switch_once(system_lang_switch_combo, logger):
    """
    Отправляет системную комбинацию переключения языка ОДИН РАЗ.
    Не ждёт подтверждения — это делает вызывающий код позже.
    Возвращает True если отправка прошла без исключений.
    """
    import keyboard
    
    release_stuck_modifiers()
    
    combo = system_lang_switch_combo or "alt+shift"
    logger.debug(f"[LAYOUT] Attempting to send lang switch combo: '{combo}'")
    try:
        keyboard.send(combo, do_press=True, do_release=True)
        logger.debug("[LAYOUT] Combo sent successfully.")
        return True
    except Exception as e:
        logger.error(f"Lang switch send failed ({combo}): {e}")
        return False