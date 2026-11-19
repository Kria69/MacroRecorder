"""Всплывающая подсказка с возможностью обновления текста."""

from PyQt6.QtCore import Qt, QTimer, QObject, QPoint, QEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from ..theme import THEMES, CURRENT_THEME


class LightToolTip(QObject):
    def __init__(self, widget, text):
        super().__init__(widget)
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.show)
        self.widget.installEventFilter(self)

    def _tooltip_style(self):
        return f"""
            background-color: {THEMES[CURRENT_THEME]['TOOLTIP_BG']};
            color: white;
            border-radius: 8px;
            padding: 8px 12px;
            font-family: Arial;
            font-size: 11px;
        """

    def eventFilter(self, obj, event):
        if obj == self.widget:
            if event.type() == QEvent.Type.Enter:
                self.timer.start()
            elif event.type() == QEvent.Type.Leave:
                self.timer.stop()
                self.hide()
        return super().eventFilter(obj, event)

    def show(self):
        if self.tooltip_window is not None or not self.text:
            return
        pos = self.widget.mapToGlobal(QPoint(20, self.widget.height() + 10))
        self.tooltip_window = QWidget(None, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.tooltip_window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self.tooltip_window)
        layout.setContentsMargins(6, 6, 6, 6)

        lbl = QLabel(self.text, self.tooltip_window)
        lbl.setStyleSheet(self._tooltip_style())
        layout.addWidget(lbl)
        self.tooltip_window.adjustSize()
        self.tooltip_window.move(pos)
        self.tooltip_window.show()

    def hide(self):
        if self.tooltip_window:
            self.tooltip_window.close()
            self.tooltip_window.deleteLater()
            self.tooltip_window = None

    def update_text(self, new_text):
        """Обновляет текст подсказки без пересоздания объекта."""
        self.text = new_text
        if self.tooltip_window:
            lbl = self.tooltip_window.findChild(QLabel)
            if lbl:
                lbl.setText(new_text)
                lbl.setStyleSheet(self._tooltip_style())
                self.tooltip_window.adjustSize()