# lab02_katar_method_wide.py
# Требуется: pip install PySide6
import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF

class RulerWidget(QFrame):
    def __init__(self, length_mm=200, px_per_mm=2.5, parent=None):
        super().__init__(parent)
        self.length_mm = length_mm
        self.px_per_mm = px_per_mm
        self.setMinimumWidth(int(self.length_mm * self.px_per_mm) + 60)
        self.setMinimumHeight(120)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        left = 20
        top = 20
        # draw ruler body
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QColor(245, 245, 220))
        painter.drawRect(left, top, int(self.length_mm * self.px_per_mm), 30)
        # ticks and labels
        painter.setPen(QPen(Qt.black, 1))
        font = QFont("Sans", 9)
        painter.setFont(font)
        for mm in range(0, self.length_mm + 1):
            x = left + mm * self.px_per_mm
            if mm % 10 == 0:
                painter.drawLine(x, top + 30, x, top + 30 + 14)
                painter.drawText(x - 12, top + 30 + 32, f"{mm}")
            elif mm % 5 == 0:
                painter.drawLine(x, top + 30, x, top + 30 + 9)
            else:
                painter.drawLine(x, top + 30, x, top + 30 + 5)

class BallsRowWidget(QFrame):
    def __init__(self, ruler_widget: RulerWidget, parent=None):
        super().__init__(parent)
        self.ruler = ruler_widget
        self.setMinimumSize(700, 260)
        self.balls = []
        self.ball_radius = 12
        self.row_y = 150
        self.drag_index = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        self._create_random_row()

    def _create_random_row(self):
        n = random.randint(6, 12)
        left = 40
        right = max(self.width() - 40, left + int(self.ruler.length_mm * self.ruler.px_per_mm))
        spacing = (right - left) / (n + 1)
        self.balls = []
        for i in range(n):
            x = left + (i + 1) * spacing + random.uniform(-10, 10)
            y = self.row_y + random.uniform(-6, 6)
            self.balls.append({'pos': QPointF(x, y), 'r': self.ball_radius, 'target_x': x})

    def resizeEvent(self, event):
        w = self.width()
        for b in self.balls:
            if b['pos'].x() > w - 20:
                b['pos'].setX(w - 20)
                b['target_x'] = b['pos'].x()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        painter.setPen(QPen(Qt.gray, 1, Qt.DashLine))
        painter.drawLine(10, self.row_y, self.width() - 10, self.row_y)
        for i, b in enumerate(self.balls):
            pos = b['pos']
            r = b['r']
            painter.setBrush(QColor(0, 0, 0, 30))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(pos.x()+3, pos.y()+5), r+3, r+3)
            painter.setBrush(QColor(200, 80, 80))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawEllipse(pos, r, r)
            painter.setPen(QPen(Qt.black, 1))
            painter.setFont(QFont("Sans", 9))
            painter.drawText(pos.x()-5, pos.y()+5, str(i+1))
        if len(self.balls) >= 2:
            xs = sorted([b['pos'].x() for b in self.balls])
            left_x = xs[0]
            right_x = xs[-1]
            painter.setPen(QPen(QColor(40, 120, 200), 2))
            painter.drawLine(left_x, self.row_y - 24, right_x, self.row_y - 24)
            painter.setFont(QFont("Sans", 11, QFont.Bold))
            painter.drawText((left_x + right_x)/2 - 18, self.row_y - 30, "L")
            painter.setPen(QPen(QColor(40, 120, 200), 2))
            painter.drawLine(left_x, self.row_y - 28, left_x, self.row_y - 20)
            painter.drawLine(right_x, self.row_y - 28, right_x, self.row_y - 20)

    def mousePressEvent(self, event):
        p = event.position()
        for i, b in enumerate(self.balls):
            if (b['pos'] - p).manhattanLength() <= b['r'] + 6:
                self.drag_index = i
                return
        x = p.x()
        y = self.row_y
        self.balls.append({'pos': QPointF(x, y), 'r': self.ball_radius, 'target_x': x})
        self.update()

    def mouseMoveEvent(self, event):
        if self.drag_index is None:
            return
        p = event.position()
        x = p.x()
        x = max(20, min(self.width() - 20, x))
        self.balls[self.drag_index]['pos'].setX(x)
        self.balls[self.drag_index]['pos'].setY(self.row_y)
        self.balls[self.drag_index]['target_x'] = x
        self.update()

    def mouseReleaseEvent(self, event):
        self.drag_index = None
        self._snap_to_row()

    def _snap_to_row(self):
        if len(self.balls) < 2:
            return
        self.balls.sort(key=lambda b: b['pos'].x())
        left = self.balls[0]['pos'].x()
        right = self.balls[-1]['pos'].x()
        n = len(self.balls)
        if right - left < 1:
            return
        spacing = (right - left) / (n - 1)
        for i, b in enumerate(self.balls):
            b['target_x'] = left + i * spacing

    def animate(self):
        changed = False
        for b in self.balls:
            tx = b.get('target_x', b['pos'].x())
            dx = tx - b['pos'].x()
            if abs(dx) > 0.5:
                b['pos'].setX(b['pos'].x() + dx * 0.25)
                changed = True
            else:
                b['pos'].setX(tx)
        if changed:
            self.update()

    def clear(self):
        self.balls = []
        self.update()

    def randomize(self):
        self._create_random_row()
        self.update()

    def measured_length_mm(self):
        if len(self.balls) < 2:
            return 0.0
        xs = sorted([b['pos'].x() for b in self.balls])
        left_x = xs[0]
        right_x = xs[-1]
        px_dist = right_x - left_x
        mm = px_dist / self.ruler.px_per_mm
        return max(0.0, mm)

    def count_balls(self):
        return len(self.balls)

class Lab02App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная №2 — Катарный метод измерения размеров")
        # Увеличенная ширина окна
        self.setMinimumSize(1200, 600)

        self.ruler_length_mm = random.choice([150, 200, 250])
        self.px_per_mm = 2.5

        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 0)

        self.ruler = RulerWidget(length_mm=self.ruler_length_mm, px_per_mm=self.px_per_mm)
        left_layout.addWidget(self.ruler)

        self.balls_widget = BallsRowWidget(self.ruler)
        left_layout.addWidget(self.balls_widget, 1)

        lbl_title = QLabel("<b>Катарный метод измерения</b>")
        right_layout.addWidget(lbl_title)

        self.lbl_params = QLabel(
            f"Длина линейки: <b>{self.ruler_length_mm} мм</b>\n"
            "Добавляйте шарики кликом, перетаскивайте их мышью.\n"
            "Нажмите «Выравнять ряд» для аккуратного ряда."
        )
        self.lbl_params.setWordWrap(True)
        right_layout.addWidget(self.lbl_params)

        self.lbl_measured = QLabel("L = 0.0 мм\nN = 0\nd = 0.0 мм")
        right_layout.addWidget(self.lbl_measured)

        btn_random = QPushButton("Случайный ряд")
        btn_random.clicked.connect(self.on_random)
        btn_clear = QPushButton("Очистить")
        btn_clear.clicked.connect(self.on_clear)
        btn_snap = QPushButton("Выравнять ряд")
        btn_snap.clicked.connect(self.on_snap)
        right_layout.addWidget(btn_random)
        right_layout.addWidget(btn_clear)
        right_layout.addWidget(btn_snap)

        right_layout.addSpacing(8)
        right_layout.addWidget(QLabel("<b>Ввод ответов</b>"))
        self.input_L = QLineEdit()
        self.input_L.setPlaceholderText("Введите L, мм")
        self.input_N = QLineEdit()
        self.input_N.setPlaceholderText("Введите N, шт")
        self.input_d = QLineEdit()
        self.input_d.setPlaceholderText("Введите d, мм (L/N)")
        right_layout.addWidget(self.input_L)
        right_layout.addWidget(self.input_N)
        right_layout.addWidget(self.input_d)

        btn_check = QPushButton("Проверить")
        btn_check.clicked.connect(self.on_check)
        btn_show = QPushButton("Показать ответ")
        btn_show.clicked.connect(self.on_show)
        right_layout.addWidget(btn_check)
        right_layout.addWidget(btn_show)

        self.lbl_result = QLabel("")
        self.lbl_result.setWordWrap(True)
        right_layout.addWidget(self.lbl_result)
        right_layout.addStretch(1)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_measured)
        self.update_timer.start(200)

    def on_random(self):
        self.balls_widget.randomize()

    def on_clear(self):
        self.balls_widget.clear()

    def on_snap(self):
        self.balls_widget._snap_to_row()

    def update_measured(self):
        L = self.balls_widget.measured_length_mm()
        N = self.balls_widget.count_balls()
        d = (L / N) if N > 0 else 0.0
        self.lbl_measured.setText(f"L = {L:.1f} мм\nN = {N}\nd = {d:.3f} мм")

    def on_check(self):
        try:
            user_L = float(self.input_L.text())
            user_N = int(float(self.input_N.text()))
            user_d = float(self.input_d.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения в поля L, N, d.")
            return
        true_L = self.balls_widget.measured_length_mm()
        true_N = self.balls_widget.count_balls()
        true_d = (true_L / true_N) if true_N > 0 else 0.0
        tol_L = max(0.5, true_L * 0.01)
        tol_N = 0
        tol_d = max(0.01, true_d * 0.02)
        ok_L = abs(user_L - true_L) <= tol_L
        ok_N = (user_N == true_N)
        ok_d = abs(user_d - true_d) <= tol_d
        lines = []
        if ok_L:
            lines.append("✅ L рассчитано верно.")
        else:
            lines.append(f"❌ L неверно. Правильно: {true_L:.1f} мм (допуск ±{tol_L:.2f} мм).")
        if ok_N:
            lines.append("✅ N рассчитано верно.")
        else:
            lines.append(f"❌ N неверно. Правильно: {true_N} шт.")
        if ok_d:
            lines.append("✅ d рассчитано верно.")
        else:
            lines.append(f"❌ d неверно. Правильно: {true_d:.3f} мм (допуск ±{tol_d:.3f} мм).")
        self.lbl_result.setText("\n".join(lines))

    def on_show(self):
        true_L = self.balls_widget.measured_length_mm()
        true_N = self.balls_widget.count_balls()
        true_d = (true_L / true_N) if true_N > 0 else 0.0
        self.input_L.setText(f"{true_L:.2f}")
        self.input_N.setText(str(true_N))
        self.input_d.setText(f"{true_d:.4f}")
        self.lbl_result.setText("Показаны правильные значения.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Lab02App()
    win.show()
    sys.exit(app.exec())
