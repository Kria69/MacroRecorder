"""Утилиты хоткеев: англофикация отображения, запрет Space/Win."""

import ctypes
import keyboard


def get_us_layout(logger=None):
    """Получает хэндл английской (US) раскладки клавиатуры."""
    try:
        us_hkl = ctypes.windll.user32.LoadKeyboardLayoutW("00000409", 0)
        if us_hkl:
            if logger: logger.debug(f"[HOTKEY_UTILS] US Layout loaded successfully: {hex(us_hkl)}")
            return us_hkl
    except Exception as e:
        if logger: logger.error(f"[HOTKEY_UTILS] Failed to load US layout: {e}")
    return None


def scan_code_to_us_name(scan_code, logger=None):
    """Преобразует скан-код клавиши в имя клавиши английской (US) раскладки."""
    try:
        us_hkl = get_us_layout(logger)
        if us_hkl is None:
            if logger: logger.warning("[HOTKEY_UTILS] Cannot convert scan code: US layout not available.")
            return None

        vk = ctypes.windll.user32.MapVirtualKeyExW(scan_code, 3, us_hkl)
        if vk == 0:
            if logger: logger.debug(f"[HOTKEY_UTILS] MapVirtualKeyExW returned 0 for scan_code {scan_code}")
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
            name = special_vk_names[vk]
            if logger: logger.debug(f"[HOTKEY_UTILS] Scan code {scan_code} mapped to special VK name: '{name}'")
            return name

        if 0x70 <= vk <= 0x87:
            name = f'f{vk - 0x6F}'
            if logger: logger.debug(f"[HOTKEY_UTILS] Scan code {scan_code} mapped to function key: '{name}'")
            return name
            
        if 0x30 <= vk <= 0x39:
            name = chr(vk)
            if logger: logger.debug(f"[HOTKEY_UTILS] Scan code {scan_code} mapped to number: '{name}'")
            return name
            
        if 0x41 <= vk <= 0x5A:
            name = chr(vk).lower()
            if logger: logger.debug(f"[HOTKEY_UTILS] Scan code {scan_code} mapped to letter: '{name}'")
            return name

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
                name = oem_names[ch]
                if logger: logger.debug(f"[HOTKEY_UTILS] Scan code {scan_code} mapped to OEM char: '{name}'")
                return name
            name = ch.lower()
            if logger: logger.debug(f"[HOTKEY_UTILS] Scan code {scan_code} mapped to unicode char: '{name}'")
            return name

        if logger: logger.debug(f"[HOTKEY_UTILS] ToUnicodeEx failed for scan_code {scan_code}, VK={vk}")
        return None
    except Exception as e:
        if logger: logger.error(f"[HOTKEY_UTILS] Exception in scan_code_to_us_name: {e}")
        return None


def hotkey_to_english(hotkey_str, logger=None):
    """Преобразует строку хоткея так, чтобы все клавиши отображались в английской раскладке."""
    if not hotkey_str:
        return hotkey_str

    if logger: logger.debug(f"[HOTKEY_UTILS] Converting hotkey to English: '{hotkey_str}'")
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
            if logger: logger.debug(f"[HOTKEY_UTILS] Part '{part}' is a known name, kept as is.")
            continue

        if part_lower.startswith('f') and part_lower[1:].isdigit():
            converted_parts.append(part_lower)
            if logger: logger.debug(f"[HOTKEY_UTILS] Part '{part}' is a function key, kept as is.")
            continue

        if len(part_lower) == 1 and part_lower.isascii():
            converted_parts.append(part_lower)
            if logger: logger.debug(f"[HOTKEY_UTILS] Part '{part}' is a single ASCII char, kept as is.")
            continue

        try:
            scan_codes = keyboard.key_to_scan_codes(part_lower)
            if scan_codes:
                us_name = scan_code_to_us_name(scan_codes[0], logger)
                if us_name:
                    converted_parts.append(us_name)
                    if logger: logger.debug(f"[HOTKEY_UTILS] Part '{part}' converted via scan code to '{us_name}'")
                    continue
                else:
                    if logger: logger.warning(f"[HOTKEY_UTILS] Could not map scan code for '{part}'")
        except Exception as e:
            if logger: logger.warning(f"[HOTKEY_UTILS] Failed to get scan codes for '{part}': {e}")

        converted_parts.append(part_lower)
        if logger: logger.debug(f"[HOTKEY_UTILS] Part '{part}' could not be converted, kept original.")

    result = '+'.join(converted_parts)
    if logger: logger.debug(f"[HOTKEY_UTILS] Final converted hotkey: '{result}'")
    return result


def contains_forbidden_keys(hotkey_str, logger=None):
    """Проверяет, содержит ли комбинация запрещённые клавиши Space или Win."""
    if not hotkey_str:
        return False

    if logger: logger.debug(f"[HOTKEY_UTILS] Checking for forbidden keys in: '{hotkey_str}'")
    
    forbidden_names = {
        'space', 'spacebar', ' ',
        'win', 'windows', 'left windows', 'right windows',
        'left win', 'right win', 'lwin', 'rwin',
        'super', 'left super', 'right super', 'meta', 'left meta', 'right meta',
    }

    for part in hotkey_str.split('+'):
        part_lower = part.strip().lower()
        if part_lower in forbidden_names:
            if logger: logger.warning(f"[HOTKEY_UTILS] Forbidden key found by name: '{part_lower}'")
            return True

        try:
            scan_codes = keyboard.key_to_scan_codes(part_lower)
            for sc in scan_codes:
                us_name = scan_code_to_us_name(sc, logger)
                if us_name and us_name.lower() in forbidden_names:
                    if logger: logger.warning(f"[HOTKEY_UTILS] Forbidden key found by scan code: '{us_name}'")
                    return True
        except Exception:
            pass

    if logger: logger.debug("[HOTKEY_UTILS] No forbidden keys found.")
    return False