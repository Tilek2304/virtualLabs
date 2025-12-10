# lab_power_lamp.py
# Требуется: pip install PySide6
import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer, QPointF

# Универсальный аналоговый прибор
class MeterWidget(QFrame):
    def __init__(self, kind="A", parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.kind = kind
        self.value = 0.0
        self.max_display = 1.0

    def set_value(self, val, vmax=None):
        self.value = val if val is not None else 0.0
        if vmax is not None:
            self.max_display = max(1e-6, float(vmax))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        radius = min(w, h) // 2 - 8

        p.fillRect(self.rect(), QColor(250, 250, 250))
        p.setPen(QPen(Qt.black, 2))
        p.setBrush(QColor(255, 255, 255))
        p.drawEllipse(cx - radius, cy - radius, 2 * radius, 2 * radius)

        p.setPen(QPen(Qt.black, 1))
        for angle in range(-60, 61, 10):
            rad = math.radians(angle)
            x0 = cx + int((radius - 8) * math.cos(rad))
            y0 = cy - int((radius - 8) * math.sin(rad))
            x1 = cx + int(radius * math.cos(rad))
            y1 = cy - int(radius * math.sin(rad))
            p.drawLine(x0, y0, x1, y1)

        frac = 0.0
        if self.max_display > 0:
            frac = max(0.0, min(1.0, self.value / self.max_display))
        angle = -60 + frac * 120.0
        rad = math.radians(angle)
        p.setPen(QPen(QColor(200, 30, 30), 2))
        x_end = cx + int((radius - 14) * math.cos(rad))
        y_end = cy - int((radius - 14) * math.sin(rad))
        p.drawLine(cx, cy, x_end, y_end)

        p.setPen(QPen(Qt.black, 2))
        p.setFont(QFont("Sans", 12, QFont.Bold))
        p.drawText(cx - 8, cy + 6, self.kind)
        p.setFont(QFont("Sans", 9))
        if self.kind == "A":
            p.drawText(8, h - 10, f"{self.value:.3f} A / {self.max_display:.3f}")
        else:
            p.drawText(8, h - 10, f"{self.value:.2f} V / {self.max_display:.2f}")

# Визуальная лампа с яркостью по мощности
class LampWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.brightness = 0.0  # 0..1

    def set_brightness(self, b):
        self.brightness = max(0.0, min(1.0, b))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250, 250, 250))

        cx, cy = w // 2, h // 2 - 10
        radius = min(w, h) // 4

        glow = int(120 + 135 * self.brightness)
        core_color = QColor(255, 220 - int(80 * (1 - self.brightness)), 80)
        p.setPen(QPen(Qt.black, 1))
        # glow
        for i in range(6, 0, -1):
            alpha = int(30 * (i / 6.0) * self.brightness)
            p.setBrush(QColor(255, 230, 120, alpha))
            p.drawEllipse(cx - radius - i * 6, cy - radius - i * 6, 2 * (radius + i * 6), 2 * (radius + i * 6))
        # bulb
        p.setBrush(core_color)
        p.drawEllipse(cx - radius, cy - radius, 2 * radius, 2 * radius)
        # filament
        p.setPen(QPen(Qt.darkGray, 2))
        p.drawArc(cx - radius // 2, cy - 6, radius, 12, 0, 180 * 16)
        # base
        p.setBrush(QColor(160, 160, 160))
        p.drawRect(cx - radius // 2, cy + radius - 6, radius, 18)
        # label power
        p.setPen(QPen(Qt.black, 1))
        p.setFont(QFont("Sans", 10))
        p.drawText(10, h - 10, f"Ярктыгы {self.brightness*100:.0f}%")

# Схема с батареей и лампой
class CircuitWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 240)
        self.U = 6.0
        self.R_lamp = 10.0
        self.R_internal = 1.0
        self.I = None
        self.P = None
        self._recalc()

    def set_params(self, U, R_lamp, R_internal=1.0):
        self.U = float(U)
        self.R_lamp = float(R_lamp)
        self.R_internal = float(R_internal)
        self._recalc()
        self.update()

    def set_U(self, U):
        self.U = float(U)
        self._recalc()
        self.update()

    def set_Rlamp(self, R):
        self.R_lamp = float(R)
        self._recalc()
        self.update()

    def _recalc(self):
        R_total = self.R_lamp + self.R_internal
        if R_total <= 1e-9:
            self.I = None
            self.P = None
        else:
            self.I = self.U / R_total
            self.P = self.U * self.I  # мощность источника, мощность на лампе близка к I^2 * R_lamp
            # мощность на лампе
            self.P_lamp = (self.I ** 2) * self.R_lamp

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(245, 245, 245))

        mid_y = h // 2
        left_x = 40
        right_x = w - 160

        # батарея
        p.setPen(QPen(Qt.black, 2))
        p.setBrush(QColor(200, 200, 200))
        p.drawRect(left_x, mid_y - 18, 10, 36)
        p.setBrush(QColor(220, 220, 220))
        p.drawRect(left_x + 18, mid_y - 28, 10, 56)
        p.setPen(QPen(QColor(200, 30, 30), 3))
        p.drawLine(left_x + 28, mid_y, left_x + 100, mid_y)

        # лампа как резистор
        x = left_x + 100
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(x, mid_y, x + 40, mid_y)
        lamp_cx = x + 80
        p.setBrush(QColor(255, 235, 120))
        p.drawEllipse(lamp_cx - 28, mid_y - 28, 56, 56)
        p.setPen(QPen(Qt.black, 1))
        p.setFont(QFont("Sans", 9))
        p.drawText(lamp_cx - 22, mid_y + 40, f"R={self.R_lamp:.1f}Ω")

        # провод к амперметру
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(lamp_cx + 28, mid_y, right_x, mid_y)

        # амперметр справа
        ax = right_x + 40
        ay = mid_y
        p.setBrush(QColor(255, 255, 255))
        p.setPen(QPen(Qt.black, 2))
        p.drawEllipse(ax - 36, ay - 36, 72, 72)
        p.setFont(QFont("Sans", 10))
        if self.I is not None:
            p.drawText(ax - 28, ay - 46, f"I = {self.I:.3f} A")
        else:
            p.drawText(ax - 28, ay - 46, "I = — A")

        # нижняя ветвь замыкание
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(ax + 36, ay, ax + 36, ay + 80)
        p.drawLine(ax + 36, ay + 80, left_x + 10, ay + 80)
        p.drawLine(left_x + 10, ay + 80, left_x + 10, mid_y - 6)
        p.drawLine(left_x + 10, mid_y - 6, left_x + 2, mid_y - 6)
        p.drawLine(left_x + 2, mid_y - 6, left_x + 2, mid_y + 6)
        p.drawLine(left_x + 2, mid_y + 6, left_x + 10, mid_y + 6)

        # подписи
        p.setFont(QFont("Sans", 10))
        p.drawText(12, mid_y - 40, f"Uист = {self.U:.2f} В")
        if hasattr(self, "P_lamp"):
            p.drawText(12, mid_y - 24, f"P чырак = {self.P_lamp:.3f} Вт")

# Главное приложение
class LabPowerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык — Чырактагы ток жана жумуш")
        self.setMinimumSize(1000, 640)

        main = QHBoxLayout(self)
        left = QVBoxLayout()
        right = QVBoxLayout()
        main.addLayout(left, 2)
        main.addLayout(right, 1)

        # виджеты слева
        self.circuit = CircuitWidget()
        left.addWidget(self.circuit)

        meters_row = QHBoxLayout()
        self.ammeter = MeterWidget("A")
        self.voltmeter = MeterWidget("V")
        meters_row.addWidget(self.ammeter)
        meters_row.addWidget(self.voltmeter)
        left.addLayout(meters_row)

        self.lamp = LampWidget()
        left.addWidget(self.lamp)

        # правая панель
        right.addWidget(QLabel("<b>Чырактагы ток жана жумуш</b>"))
        info = QLabel(
            "Булак чыңдыгын жана чырактын каршылыгын орнотуңуз.\n"
            "Жумушту аяктоо үчүн \"Баштоо\" баскычын басыңыз жана убактысын эсептеп салыңыз.\n"
            "Формулалар P = U·I жана A = P·t."
        )
        info.setWordWrap(True)
        right.addWidget(info)

        right.addWidget(QLabel("<b>Параметрлер</b>"))
        self.input_U = QLineEdit(); self.input_U.setPlaceholderText("U булак В")
        self.input_R = QLineEdit(); self.input_R.setPlaceholderText("R чырак Ом")
        self.input_Rint = QLineEdit(); self.input_Rint.setPlaceholderText("R ички Ом")
        right.addWidget(self.input_U)
        right.addWidget(self.input_R)
        right.addWidget(self.input_Rint)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Секундомер</b>"))
        self.lbl_time = QLabel("t = 0.00 с")
        right.addWidget(self.lbl_time)

        # кнопки управления
        btn_apply = QPushButton("Параметрлерди колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        btn_start = QPushButton("Баштоо")
        btn_start.clicked.connect(self.start)
        btn_stop = QPushButton("Токтоо")
        btn_stop.clicked.connect(self.stop)
        btn_reset_timer = QPushButton("Таймерди сброс кылуу")
        btn_reset_timer.clicked.connect(self.reset_timer)
        right.addWidget(btn_apply)
        right.addWidget(btn_start)
        right.addWidget(btn_stop)
        right.addWidget(btn_reset_timer)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Өлчөөлөр жана жоопtor</b>"))
        self.input_P = QLineEdit(); self.input_P.setPlaceholderText("P Вт — сиздин эсептөөңүз")
        self.input_A = QLineEdit(); self.input_A.setPlaceholderText("A Дж — сиздин эсептөөңүз")
        right.addWidget(self.input_P)
        right.addWidget(self.input_A)

        btn_measure = QPushButton("Приборлорду өлчөө")
        btn_measure.clicked.connect(self.measure)
        btn_check = QPushButton("P жана A текшерүү")
        btn_check.clicked.connect(self.check_answers)
        btn_show = QPushButton("Туура маанилерди көрсөтүү")
        btn_show.clicked.connect(self.show_answers)
        btn_random = QPushButton("Кездейсоқ таажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        btn_reset = QPushButton("Сброс")
        btn_reset.clicked.connect(self.reset_all)

        right.addWidget(btn_measure)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        self.lbl_result = QLabel("")
        right.addWidget(self.lbl_result)
        right.addStretch(1)

        # таймер и управление мощностью
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.elapsed = 0.0
        self.running = False

        # стартовые значения
        self.random_experiment()

    def _tick(self):
        if self.running:
            self.elapsed += 0.1
            self.lbl_time.setText(f"t = {self.elapsed:.2f} с")

    def apply_params(self):
        try:
            U = float(self.input_U.text())
            R = float(self.input_R.text())
            Rint = float(self.input_Rint.text()) if self.input_Rint.text().strip() else 1.0
        except Exception:
            QMessageBox.warning(self, "Ката", "U, R, Rint үчүн сандык маанилерди киргизиңиз.")
            return
        self.circuit.set_params(U, R, Rint)
        self.ammeter.set_value(self.circuit.I if self.circuit.I is not None else 0.0, vmax=max(0.1, (self.circuit.U / max(1.0, R+Rint))))
        self.voltmeter.set_value(self.circuit.U, vmax=max(0.1, U))
        self._update_lamp()

    def _update_lamp(self):
        if self.circuit.P_lamp is not None:
            self.lamp.set_brightness(min(1.0, self.circuit.P_lamp / 2.0))

    def start(self):
        self.running = True
        self.timer.start(100)

    def stop(self):
        self.running = False
        self.timer.stop()

    def reset_timer(self):
        self.elapsed = 0.0
        self.lbl_time.setText("t = 0.00 с")
        self.running = False
        self.timer.stop()

    def measure(self):
        if self.circuit.I is None:
            QMessageBox.information(self, "Инфо", "Адегечү параметрлерди колдонуңуз.")
            return
        self.ammeter.set_value(self.circuit.I, vmax=max(0.1, (self.circuit.U / max(1.0, self.circuit.R_lamp+self.circuit.R_internal))))
        self.voltmeter.set_value(self.circuit.U, vmax=max(0.1, self.circuit.U))
        self._update_lamp()
        self.lbl_result.setText("Приборлор жаңыртылды.")

    def check_answers(self):
        try:
            P_user = float(self.input_P.text())
            A_user = float(self.input_A.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "P жана A үчүн сандык маанилерди киргизиңиз.")
            return
        P_true = self.circuit.P_lamp if self.circuit.P_lamp is not None else 0.0
        A_true = P_true * self.elapsed
        tol_P = max(0.05 * P_true, 0.01)
        tol_A = max(0.05 * A_true, 0.5)
        ok_P = abs(P_user - P_true) <= tol_P
        ok_A = abs(A_user - A_true) <= tol_A
        lines = []
        if ok_P:
            lines.append("✅ P туура.")
        else:
            lines.append(f"❌ P туура эмес. Туура: {P_true:.3f} Вт")
        if ok_A:
            lines.append("✅ A туура.")
        else:
            lines.append(f"❌ A туура эмес. Туура: {A_true:.2f} Дж")
        self.lbl_result.setText("\n".join(lines))

    def show_answers(self):
        P_true = self.circuit.P_lamp if self.circuit.P_lamp is not None else 0.0
        A_true = P_true * self.elapsed
        self.input_P.setText(f"{P_true:.3f}")
        self.input_A.setText(f"{A_true:.2f}")
        self.lbl_result.setText("Туура маанилер көрсөтүлдү.")

    def random_experiment(self):
        U = random.choice([3.0, 4.5, 6.0, 9.0, 12.0])
        R = random.uniform(5.0, 30.0)
        Rint = random.uniform(0.5, 2.0)
        self.input_U.setText(f"{U:.1f}")
        self.input_R.setText(f"{R:.2f}")
        self.input_Rint.setText(f"{Rint:.2f}")
        self.circuit.set_params(U, R, Rint)
        self._update_lamp()
        self.input_P.clear(); self.input_A.clear()
        self.lbl_result.setText("Кездейсоқ таажрыйба түзүлдү.")

    def reset_all(self):
        self.input_U.clear(); self.input_R.clear(); self.input_Rint.clear()
        self.input_P.clear(); self.input_A.clear()
        self.reset_timer()
        self.circuit.set_params(6.0, 10.0, 1.0)
        self.ammeter.set_value(0.0, vmax=1.0)
        self.voltmeter.set_value(0.0, vmax=6.0)
        self.lamp.set_brightness(0.0)
        self.lbl_result.setText("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabPowerApp()
    win.show()
    sys.exit(app.exec())
