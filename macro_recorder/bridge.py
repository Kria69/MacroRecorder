"""Мост сигналов для потокобезопасного обновления UI."""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class Bridge(QObject):
    update_status_signal = pyqtSignal(str, str)
    log_signal = pyqtSignal(str)
    playback_started_signal = pyqtSignal()
    playback_finished_signal = pyqtSignal()


def safe_invoke(func, *args):
    """Безопасно вызывает функцию в главном потоке."""
    if args:
        QTimer.singleShot(0, lambda: func(*args))
    else:
        QTimer.singleShot(0, func)