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

        # Жарыктык (свечение)
        glow = int(120 + 135 * self.brightness)
        core_color = QColor(255, 220 - int(80 * (1 - self.brightness)), 80)
        p.setPen(QPen(Qt.black, 1))
        
        for i in range(6, 0, -1):
            alpha = int(30 * (i / 6.0) * self.brightness)
            p.setBrush(QColor(255, 230, 120, alpha))
            p.drawEllipse(cx - radius - i * 6, cy - radius - i * 6, 2 * (radius + i * 6), 2 * (radius + i * 6))
        
        # Лампа
        p.setBrush(core_color)
        p.drawEllipse(cx - radius, cy - radius, 2 * radius, 2 * radius)
        # Спираль
        p.setPen(QPen(Qt.darkGray, 2))
        p.drawArc(cx - radius // 2, cy - 6, radius, 12, 0, 180 * 16)
        # Негизи (цоколь)
        p.setBrush(QColor(160, 160, 160))
        p.drawRect(cx - radius // 2, cy + radius - 6, radius, 18)
        
        # Текст
        p.setPen(QPen(Qt.black, 1))
        p.setFont(QFont("Sans", 10))
        # КОТОРМО: Яркость -> Жарыктык
        p.drawText(10, h - 10, f"Жарыктык {self.brightness*100:.0f}%")

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
            self.P = self.U * self.I
            # Лампанын кубаттуулугу: I^2 * R
            self.P_lamp = (self.I ** 2) * self.R_lamp

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(245, 245, 245))

        mid_y = h // 2
        left_x = 40
        right_x = w - 160

        # Батарея
        p.setPen(QPen(Qt.black, 2))
        p.setBrush(QColor(200, 200, 200))
        p.drawRect(left_x, mid_y - 18, 10, 36)
        p.setBrush(QColor(220, 220, 220))
        p.drawRect(left_x + 18, mid_y - 28, 10, 56)
        p.setPen(QPen(QColor(200, 30, 30), 3))
        p.drawLine(left_x + 28, mid_y, left_x + 100, mid_y)

        # Лампа (резистор катары)
        x = left_x + 100
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(x, mid_y, x + 40, mid_y)
        lamp_cx = x + 80
        p.setBrush(QColor(255, 235, 120))
        p.drawEllipse(lamp_cx - 28, mid_y - 28, 56, 56)
        p.setPen(QPen(Qt.black, 1))
        p.setFont(QFont("Sans", 9))
        p.drawText(lamp_cx - 22, mid_y + 40, f"R={self.R_lamp:.1f}Ω")

        # Амперметрге зым
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(lamp_cx + 28, mid_y, right_x, mid_y)

        # Амперметр (оң жакта)
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

        # Төмөнкү зым (туюк чынжыр)
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(ax + 36, ay, ax + 36, ay + 80)
        p.drawLine(ax + 36, ay + 80, left_x + 10, ay + 80)
        p.drawLine(left_x + 10, ay + 80, left_x + 10, mid_y - 6)
        p.drawLine(left_x + 10, mid_y - 6, left_x + 2, mid_y - 6)
        p.drawLine(left_x + 2, mid_y - 6, left_x + 2, mid_y + 6)
        p.drawLine(left_x + 2, mid_y + 6, left_x + 10, mid_y + 6)

        # Подписи
        p.setFont(QFont("Sans", 10))
        p.drawText(12, mid_y - 40, f"Uбулак = {self.U:.2f} В")
        if hasattr(self, "P_lamp"):
            # КОТОРМО: P лампы -> P лампа
            p.drawText(12, mid_y - 24, f"P лампа = {self.P_lamp:.3f} Вт")

# Главное приложение
class LabPowerApp(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Мощность и работа тока в лампе -> Лампанын электр тогунун жумушу жана кубаттуулугу
        self.setWindowTitle("Лабораториялык иш — Лампанын электр тогунун жумушу жана кубаттуулугу")
        self.setMinimumSize(1000, 640)

        main = QHBoxLayout(self)
        left = QVBoxLayout()
        right = QVBoxLayout()
        main.addLayout(left, 2)
        main.addLayout(right, 1)

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

        # Правая панель
        # КОТОРМО: Заголовок
        right.addWidget(QLabel("<b>Токтун жумушу жана кубаттуулугу</b>"))
        
        # КОТОРМО: Инструкция
        info = QLabel(
            "Булактын чыңалуусун жана лампанын каршылыгын орнотуңуз.\n"
            "«Баштоо» баскычын басып, убакытты эсептөөнү баштаңыз.\n"
            "Формулалар: P = U·I жана A = P·t."
        )
        info.setWordWrap(True)
        right.addWidget(info)

        right.addWidget(QLabel("<b>Параметрлер</b>"))
        self.input_U = QLineEdit(); self.input_U.setPlaceholderText("U булак (В)")
        self.input_R = QLineEdit(); self.input_R.setPlaceholderText("R лампа (Ом)")
        self.input_Rint = QLineEdit(); self.input_Rint.setPlaceholderText("R ички (Ом)")
        right.addWidget(self.input_U)
        right.addWidget(self.input_R)
        right.addWidget(self.input_Rint)

        right.addSpacing(6)
        # КОТОРМО: Секундомер -> Секундомер
        right.addWidget(QLabel("<b>Секундомер</b>"))
        self.lbl_time = QLabel("t = 0.00 с")
        right.addWidget(self.lbl_time)

        # Кнопки
        # КОТОРМО: Применить -> Колдонуу
        btn_apply = QPushButton("Параметрлерди колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        # КОТОРМО: Запустить -> Баштоо
        btn_start = QPushButton("Баштоо")
        btn_start.clicked.connect(self.start)
        # КОТОРМО: Остановить -> Токтотуу
        btn_stop = QPushButton("Токтотуу")
        btn_stop.clicked.connect(self.stop)
        # КОТОРМО: Сброс таймера -> Таймерди тазалоо
        btn_reset_timer = QPushButton("Таймерди тазалоо")
        btn_reset_timer.clicked.connect(self.reset_timer)
        
        right.addWidget(btn_apply)
        right.addWidget(btn_start)
        right.addWidget(btn_stop)
        right.addWidget(btn_reset_timer)

        right.addSpacing(6)
        # КОТОРМО: Измерения и ответы -> Өлчөөлөр жана жооптор
        right.addWidget(QLabel("<b>Өлчөөлөр жана жооптор</b>"))
        self.input_P = QLineEdit(); self.input_P.setPlaceholderText("P (Вт) — сиздин эсептөө")
        self.input_A = QLineEdit(); self.input_A.setPlaceholderText("A (Дж) — сиздин эсептөө")
        right.addWidget(self.input_P)
        right.addWidget(self.input_A)

        # КОТОРМО: Измерить приборы -> Приборлорду өлчөө
        btn_measure = QPushButton("Приборлорду өлчөө")
        btn_measure.clicked.connect(self.measure)
        # КОТОРМО: Проверить P и A -> P жана A текшерүү
        btn_check = QPushButton("P жана A текшерүү")
        btn_check.clicked.connect(self.check_answers)
        # КОТОРМО: Показать правильные значения -> Туура маанилерди көрсөтүү
        btn_show = QPushButton("Туура маанилерди көрсөтүү")
        btn_show.clicked.connect(self.show_answers)
        # КОТОРМО: Случайный эксперимент -> Кокустан тандалган тажрыйба
        btn_random = QPushButton("Кокустан тандалган тажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        # КОТОРМО: Сброс -> Кайра баштоо
        btn_reset = QPushButton("Кайра баштоо")
        btn_reset.clicked.connect(self.reset_all)

        right.addWidget(btn_measure)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        self.lbl_result = QLabel("")
        right.addWidget(self.lbl_result)
        right.addStretch(1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.elapsed = 0.0
        self.running = False

        self.random_experiment()

    def apply_params(self):
        try:
            U = float(self.input_U.text())
            R = float(self.input_R.text())
            Rint = float(self.input_Rint.text()) if self.input_Rint.text().strip() else 1.0
        except Exception:
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "U жана R үчүн сан маанилерин киргизиңиз.")
            return
        self.circuit.set_params(U, R, Rint)
        
        self.ammeter.set_value(self.circuit.I if self.circuit.I is not None else 0.0,
                               vmax=max(0.1, self.circuit.U / max(1.0, R + Rint)))
        self.voltmeter.set_value(self.circuit.P_lamp if hasattr(self.circuit, "P_lamp") else 0.0,
                                 vmax=max(0.1, self.circuit.U))
        
        P_lamp = getattr(self.circuit, "P_lamp", 0.0)
        b = min(1.0, P_lamp / max(0.1, self.circuit.U * self.circuit.I if self.circuit.I else 0.1))
        self.lamp.set_brightness(b)
        # КОТОРМО: Параметры применены -> Параметрлер колдонулду
        self.lbl_result.setText("Параметрлер колдонулду. Убакытты өлчөөнү баштаңыз.")

    def start(self):
        if self.circuit.I is None:
            QMessageBox.information(self, "Маалымат", "Адегенде параметрлерди киргизиңиз.")
            return
        if not self.running:
            self.timer.start(100)
            self.running = True
            # КОТОРМО: Таймер запущен -> Таймер иштеди
            self.lbl_result.setText("Таймер иштеди.")

    def stop(self):
        if self.running:
            self.timer.stop()
            self.running = False
            # КОТОРМО: Таймер остановлен -> Таймер токтоду
            self.lbl_result.setText("Таймер токтоду.")

    def reset_timer(self):
        self.elapsed = 0.0
        self.lbl_time.setText("t = 0.00 с")
        # КОТОРМО: Таймер сброшен -> Таймер тазаланды
        self.lbl_result.setText("Таймер тазаланды.")

    def _tick(self):
        self.elapsed += 0.1
        self.lbl_time.setText(f"t = {self.elapsed:.2f} с")
        P_lamp = getattr(self.circuit, "P_lamp", 0.0)
        b = min(1.0, P_lamp / max(0.1, self.circuit.U * self.circuit.I if self.circuit.I else 0.1))
        self.lamp.set_brightness(b)

    def measure(self):
        if self.circuit.I is None:
            QMessageBox.information(self, "Маалымат", "Адегенде чынжырды куруңуз.")
            return
        I_meas = self.circuit.I
        U_meas = self.circuit.U
        P_lamp = getattr(self.circuit, "P_lamp", 0.0)
        self.ammeter.set_value(I_meas, vmax=max(0.1, self.circuit.U / max(1.0, self.circuit.R_lamp + self.circuit.R_internal)))
        self.voltmeter.set_value(U_meas, vmax=max(0.1, self.circuit.U))
        # КОТОРМО: Измерение -> Өлчөө, Показания -> Көрсөткүчтөр
        QMessageBox.information(self, "Өлчөө", f"Көрсөткүчтөр: I = {I_meas:.3f} A, U = {U_meas:.2f} V\nP лампа = {P_lamp:.3f} Вт")
        self.lbl_result.setText("Приборлор иштеди. P жана A маанилерин эсептеп, киргизиңиз.")

    def check_answers(self):
        try:
            P_user = float(self.input_P.text())
            A_user = float(self.input_A.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "P жана A үчүн сан маанилерин киргизиңиз.")
            return
        if self.circuit.I is None:
            QMessageBox.information(self, "Маалымат", "Адегенде чынжырды куруп, өлчөңүз.")
            return
        
        P_true = getattr(self.circuit, "P_lamp", None)
        t = self.elapsed
        A_true = P_true * t if P_true is not None else None
        
        tol_P = max(0.03 * abs(P_true) if P_true else 0.01, 0.01)
        tol_A = max(0.03 * abs(A_true) if A_true else 0.05, 0.05)
        
        okP = abs(P_user - P_true) <= tol_P
        okA = abs(A_user - A_true) <= tol_A
        
        lines = []
        if okP:
            lines.append("✅ P туура эсептелди.")
        else:
            lines.append(f"❌ P туура эмес. Туура P ≈ {P_true:.3f} Вт ( piela ±{tol_P:.3f}).")
        if okA:
            lines.append("✅ A туура эсептелди.")
        else:
            lines.append(f"❌ A туура эмес. Туура A ≈ {A_true:.3f} Дж ( piela ±{tol_A:.3f}).")
        
        self.lbl_result.setText("\n".join(lines))

    def show_answers(self):
        if self.circuit.I is None:
            QMessageBox.information(self, "Маалымат", "Адегенде чынжырды куруңуз.")
            return
        P_true = getattr(self.circuit, "P_lamp", 0.0)
        A_true = P_true * self.elapsed
        self.input_P.setText(f"{P_true:.3f}")
        self.input_A.setText(f"{A_true:.3f}")
        self.lbl_result.setText("Туура маанилер көрсөтүлдү.")

    def random_experiment(self):
        U = random.choice([3.0, 4.5, 6.0, 9.0, 12.0])
        Rlamp = random.uniform(2.0, 40.0)
        Rint = random.uniform(0.5, 3.0)
        self.input_U.setText(f"{U:.1f}")
        self.input_R.setText(f"{Rlamp:.2f}")
        self.input_Rint.setText(f"{Rint:.2f}")
        self.circuit.set_params(U, Rlamp, Rint)
        
        self.ammeter.set_value(self.circuit.I if self.circuit.I is not None else 0.0,
                               vmax=max(0.1, self.circuit.U / max(1.0, Rlamp + Rint)))
        self.voltmeter.set_value(self.circuit.U, vmax=max(0.1, self.circuit.U))
        
        self.lamp.set_brightness(min(1.0, getattr(self.circuit, "P_lamp", 0.0) / max(0.1, self.circuit.U * (self.circuit.I or 0.1))))
        self.elapsed = 0.0
        self.lbl_time.setText("t = 0.00 с")
        self.input_P.clear(); self.input_A.clear()
        self.lbl_result.setText("Жаңы тажрыйба даярдалды.")

    def reset_all(self):
        self.input_U.clear(); self.input_R.clear(); self.input_Rint.clear()
        self.input_P.clear(); self.input_A.clear()
        self.circuit.set_params(0.0, 10.0, 1.0)
        self.ammeter.set_value(0.0, vmax=1.0)
        self.voltmeter.set_value(0.0, vmax=5.0)
        self.lamp.set_brightness(0.0)
        self.elapsed = 0.0
        self.lbl_time.setText("t = 0.00 с")
        self.lbl_result.setText("Тазаланды.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabPowerApp()
    win.show()
    sys.exit(app.exec())