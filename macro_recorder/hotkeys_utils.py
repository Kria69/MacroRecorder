"""Утилиты хоткеев: англофикация отображения, запрет Space/Win."""

import ctypes
import keyboard


def get_us_layout():
    """Получает хэндл английской (US) раскладки клавиатуры."""
    try:
        us_hkl = ctypes.windll.user32.LoadKeyboardLayoutW("00000409", 0)
        if us_hkl:
            return us_hkl
    except Exception:
        pass
    return None


def scan_code_to_us_name(scan_code):
    """Преобразует скан-код клавиши в имя клавиши английской (US) раскладки."""
    try:
        us_hkl = get_us_layout()
        if us_hkl is None:
            return None

        vk = ctypes.windll.user32.MapVirtualKeyExW(scan_code, 3, us_hkl)
        if vk == 0:
            return None

        special_vk_names = {
            0x08: 'backspace', 0x09: 'tab', 0x0D: 'enter', 0x13: 'pause',
            0x14: 'caps lock', 0x1B: 'esc', 0x20: 'space',
            0x21: 'page up', 0x22: 'page down', 0x23: 'end', 0x24: 'home',
            0x25: 'left', 0x26: 'up', 0x27: 'right', 0x28: 'down',
            0x2C: 'print screen', 0x2D: 'insert', 0x2E: 'delete',
            0x5B: 'left windows', 0x5C: 'right windows', 0x5D: 'menu',
            0x60: '0', 0x61: '1', 0x62: '2', 0x63: '3', 0x64: '4',
            0x65: '5', 0x66: '6', 0x67: '7', 0x68: '8', 0x69: '9',
            0x6A: '*', 0x6B: '+', 0x6D: '-', 0x6E: '.', 0x6F: '/',
            0x90: 'num lock', 0x91: 'scroll lock',
            0xA0: 'left shift', 0xA1: 'right shift',
            0xA2: 'left ctrl', 0xA3: 'right ctrl',
            0xA4: 'left alt', 0xA5: 'right alt',
        }
        if vk in special_vk_names:
            return special_vk_names[vk]

        if 0x70 <= vk <= 0x87:
            return f'f{vk - 0x6F}'
        if 0x30 <= vk <= 0x39:
            return chr(vk)
        if 0x41 <= vk <= 0x5A:
            return chr(vk).lower()

        buf = ctypes.create_unicode_buffer(8)
        state = (ctypes.c_ubyte * 256)()
        result = ctypes.windll.user32.ToUnicodeEx(vk, scan_code, state, buf, 8, 0, us_hkl)
        if result > 0 and buf.value:
            ch = buf.value[0]
            oem_names = {
                ';': ';', ':': ';', '=': '=', '+': '=', ',': ',', '<': ',',
                '-': '-', '_': '-', '.': '.', '>': '.', '/': '/', '?': '/',
                '`': '`', '~': '`', '[': '[', '{': '[', '\\': '\\', '|': '\\',
                ']': ']', '}': ']', "'": "'",
            }
            if ch in oem_names:
                return oem_names[ch]
            return ch.lower()

        return None
    except Exception:
        return None


def hotkey_to_english(hotkey_str):
    """Преобразует строку хоткея так, чтобы все клавиши отображались в английской раскладке."""
    if not hotkey_str:
        return hotkey_str

    parts = hotkey_str.split('+')
    converted_parts = []

    for part in parts:
        part_lower = part.strip().lower()

        known_names = {
            'ctrl', 'left ctrl', 'right ctrl', 'alt', 'left alt', 'right alt',
            'shift', 'left shift', 'right shift', 'windows', 'left windows', 'right windows',
            'win', 'left win', 'right win', 'space', 'enter', 'tab', 'esc', 'escape',
            'backspace', 'delete', 'insert', 'home', 'end', 'page up', 'page down',
            'up', 'down', 'left', 'right', 'caps lock', 'num lock', 'scroll lock',
            'print screen', 'pause', 'menu', 'apps',
        }
        if part_lower in known_names:
            converted_parts.append(part_lower)
            continue

        if part_lower.startswith('f') and part_lower[1:].isdigit():
            converted_parts.append(part_lower)
            continue

        if len(part_lower) == 1 and part_lower.isascii():
            converted_parts.append(part_lower)
            continue

        try:
            scan_code = keyboard.key_to_scan_codes(part_lower)
            if scan_code:
                us_name = scan_code_to_us_name(scan_code[0])
                if us_name:
                    converted_parts.append(us_name)
                    continue
        except Exception:
            pass

        converted_parts.append(part_lower)

    return '+'.join(converted_parts)


def contains_forbidden_keys(hotkey_str):
    """Проверяет, содержит ли комбинация запрещённые клавиши Space или Win."""
    if not hotkey_str:
        return False

    forbidden_names = {
        'space', 'spacebar', ' ',
        'win', 'windows', 'left windows', 'right windows',
        'left win', 'right win', 'lwin', 'rwin',
        'super', 'left super', 'right super', 'meta', 'left meta', 'right meta',
    }

    for part in hotkey_str.split('+'):
        part_lower = part.strip().lower()
        if part_lower in forbidden_names:
            return True

        try:
            scan_codes = keyboard.key_to_scan_codes(part_lower)
            for sc in scan_codes:
                us_name = scan_code_to_us_name(sc)
                if us_name and us_name.lower() in forbidden_names:
                    return True
        except Exception:
            pass

    return False