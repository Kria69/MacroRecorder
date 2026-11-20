"""Эмуляция мыши через SendInput.

Библиотека mouse для перемещения курсора использует SetCursorPos, который меняет
позицию указателя, но не порождает поток WM_MOUSEMOVE в очередь ввода. Приложения
вроде Paint, строящие штрих по WM_MOUSEMOVE с флагом MK_LBUTTON, в таком режиме
видят только нажатие и отпускание и рисуют прямую линию между ними.

SendInput с MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE формирует полноценные события
ввода, поэтому перетаскивание воспроизводится так же, как рукой.
"""

import ctypes
from ctypes import wintypes

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000

# dwExtraInfo в winsdk объявлен как ULONG_PTR: 8 байт в x64/ARM64, 4 в x86.
# Без этого размер структуры не совпал бы с ожидаемым, и SendInput отклонил вызов.
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong
DWORD = ctypes.c_uint32
LONG = ctypes.c_int32

SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

_BUTTON_FLAGS = {
    "left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
    "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
    "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
}


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", LONG),
        ("dy", LONG),
        ("mouseData", DWORD),
        ("dwFlags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", DWORD), ("union", _INPUTUNION)]


def _send(*inputs):
    """Отправляет события ввода. Возвращает (отправлено, код ошибки)."""
    if not inputs:
        return 0, 0
    arr = (INPUT * len(inputs))(*inputs)
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    user32.SendInput.argtypes = (wintypes.UINT, ctypes.c_void_p, ctypes.c_int)
    user32.SendInput.restype = wintypes.UINT
    kernel32.GetLastError.restype = wintypes.DWORD
    sent = user32.SendInput(len(inputs), ctypes.byref(arr), ctypes.sizeof(INPUT))
    err = kernel32.GetLastError() if sent != len(inputs) else 0
    return sent, err


def _mouse_input(flags, dx=0, dy=0, data=0):
    mi = MOUSEINPUT(dx, dy, data, flags, 0, 0)
    return INPUT(type=INPUT_MOUSE, union=_INPUTUNION(mi=mi))


def _virtual_desk():
    try:
        u = ctypes.windll.user32
        left = u.GetSystemMetrics(SM_XVIRTUALSCREEN)
        top = u.GetSystemMetrics(SM_YVIRTUALSCREEN)
        width = u.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        height = u.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        if width <= 0 or height <= 0:
            raise ValueError("empty virtual screen")
        return left, top, width, height
    except Exception:
        u = ctypes.windll.user32
        return 0, 0, u.GetSystemMetrics(0) or 1, u.GetSystemMetrics(1) or 1


def _to_absolute(x, y):
    left, top, width, height = _virtual_desk()
    ax = int(round((x - left) * 65535 / max(1, width - 1)))
    ay = int(round((y - top) * 65535 / max(1, height - 1)))
    return max(0, min(65535, ax)), max(0, min(65535, ay))


def move(x, y):
    """Перемещает курсор событием ввода, а не сменой позиции указателя.

    Возвращает (отправлено, код ошибки).
    """
    ax, ay = _to_absolute(int(x), int(y))
    return _send(_mouse_input(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK, ax, ay))


def press(button="left"):
    flags = _BUTTON_FLAGS.get(button)
    if not flags:
        return 0, 0
    return _send(_mouse_input(flags[0]))


def release(button="left"):
    flags = _BUTTON_FLAGS.get(button)
    if not flags:
        return 0, 0
    return _send(_mouse_input(flags[1]))


def scroll(dy):
    if not dy:
        return 0, 0
    return _send(_mouse_input(MOUSEEVENTF_WHEEL, data=int(dy) & 0xFFFFFFFF))
