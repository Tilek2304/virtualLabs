# lab_heater_efficiency.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer

# Удельная теплоёмкость воды (Дж/(г·°C))
C_WATER = 4.2

# Универсальный аналоговый прибор (A или V)
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

# Визуализация калориметра с нагревательной спиралью
class HeaterCalorimeterWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(520, 420)
        self.m_water = 200.0
        self.t_initial = 20.0
        self.t_current = self.t_initial
        self.spiral_power = 0.0
        self.mixed = False
        self.wave_phase = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(80)

    def set_params(self, m_water, t_initial):
        self.m_water = float(m_water)
        self.t_initial = float(t_initial)
        self.t_current = self.t_initial
        self.spiral_power = 0.0
        self.update()

    def set_power(self, P_w):
        self.spiral_power = float(P_w) if P_w is not None else 0.0
        self.update()

    def heat_step(self, dt_seconds, efficiency=1.0):
        Q = self.spiral_power * dt_seconds * efficiency
        if self.m_water > 1e-9:
            delta_t = Q / (C_WATER * self.m_water)
            self.t_current += delta_t
        self.update()

    def on_timer(self):
        self.wave_phase += 0.12
        if self.wave_phase > 2 * math.pi:
            self.wave_phase -= 2 * math.pi
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))

        margin = 28
        cyl_w = int(w * 0.6)
        cyl_h = int(h * 0.6)
        cyl_x = margin
        cyl_y = margin + 10

        p.setPen(QPen(Qt.black, 2))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(cyl_x, cyl_y, cyl_w, cyl_h, 8, 8)

        inner_x = cyl_x + 8
        inner_y = cyl_y + 8
        inner_w = cyl_w - 16
        inner_h = cyl_h - 16

        water_fill = 0.70
        water_h = inner_h * water_fill
        water_y = inner_y + inner_h - water_h

        temp = self.t_current
        blue = max(60, 255 - int((temp - 10) * 2.0))
        red = min(255, 80 + int((temp - 10) * 3.0))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(red, 150, blue, 220))

        path_y = water_y
        path = []
        steps = 60
        wave_ampl = 3.0
        for i in range(steps + 1):
            t = i / steps
            x = inner_x + t * inner_w
            phase = self.wave_phase + t * 2 * math.pi
            y = path_y + math.sin(phase) * (wave_ampl * (1 - abs(2*t-1)))
            path.append((x, y))
        p.save()
        p.setBrush(QColor(red, 150, blue, 200))
        p.setPen(Qt.NoPen)
        from PySide6.QtGui import QPainterPath
        pp = QPainterPath()
        pp.moveTo(inner_x, inner_y + inner_h)
        for (x,y) in path:
            pp.lineTo(x,y)
        pp.lineTo(inner_x + inner_w, inner_y + inner_h)
        pp.closeSubpath()
        p.drawPath(pp)
        p.restore()

        spiral_cx = inner_x + inner_w * 0.5
        spiral_cy = water_y + water_h * 0.5
        p.setPen(QPen(Qt.darkGray, 2))
        p.setBrush(Qt.NoBrush)
        steps_sp = 40
        radius_max = min(inner_w, inner_h) * 0.18
        for i in range(steps_sp):
            r = radius_max * (i / steps_sp)
            angle = i * 0.6
            x = spiral_cx + r * math.cos(angle)
            y = spiral_cy + r * math.sin(angle)
            p.drawPoint(int(x), int(y))
        if self.spiral_power > 0:
            glow = min(255, int(80 + self.spiral_power * 2))
            p.setPen(QPen(QColor(255, 120, 30, min(200, glow)), 3))
            p.drawEllipse(spiral_cx - radius_max, spiral_cy - radius_max, int(2*radius_max), int(2*radius_max))

        therm_x = inner_x + inner_w + 12
        therm_y = inner_y + 8
        p.setPen(QPen(Qt.black, 1))
        p.setFont(QFont("Sans", 12, QFont.Bold))
        p.drawText(therm_x, therm_y + 20, f"T = {self.t_current:.2f} °C")
        p.setFont(QFont("Sans", 10))
        p.drawText(therm_x, therm_y + 40, f"m = {self.m_water:.0f} г")
        p.drawText(therm_x, therm_y + 58, f"Pспир = {self.spiral_power:.2f} Вт")

class LabHeaterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык — Электр нагреватель жана КПД")
        self.setMinimumSize(1100, 680)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.cal = HeaterCalorimeterWidget()
        left.addWidget(self.cal)

        meters = QHBoxLayout()
        self.voltmeter = MeterWidget("V")
        self.ammeter = MeterWidget("A")
        meters.addWidget(self.voltmeter)
        meters.addWidget(self.ammeter)
        left.addLayout(meters)

        right.addWidget(QLabel("<b>Электр нагреватель жана КПД</b>"))
        info = QLabel(
            "Модель: спираль сууда нагревает суу. Q_суу = c·m·Δt эсептеңиз,\n"
            "электр жумушу A = U·I·t жана КПД η = Q_суу / A."
        )
        info.setWordWrap(True)
        right.addWidget(info)

        right.addWidget(QLabel("<b>Таажрыйба параметрлери</b>"))
        self.input_U = QLineEdit(); self.input_U.setPlaceholderText("U (В)")
        self.input_R = QLineEdit(); self.input_R.setPlaceholderText("R спирали (Ом)")
        self.input_m = QLineEdit(); self.input_m.setPlaceholderText("m суунун (г)")
        self.input_t0 = QLineEdit(); self.input_t0.setPlaceholderText("t баштапкы (°C)")
        right.addWidget(self.input_U)
        right.addWidget(self.input_R)
        right.addWidget(self.input_m)
        right.addWidget(self.input_t0)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Секундомер</b>"))
        self.lbl_time = QLabel("t = 0.00 с")
        right.addWidget(self.lbl_time)

        btn_apply = QPushButton("Параметрлерди колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        btn_start = QPushButton("Спиралды иштетүү")
        btn_start.clicked.connect(self.start_heating)
        btn_stop = QPushButton("Спиралды өчүүчүсү")
        btn_stop.clicked.connect(self.stop_heating)
        btn_reset_timer = QPushButton("Таймерди сброс кылуу")
        btn_reset_timer.clicked.connect(self.reset_timer)
        right.addWidget(btn_apply)
        right.addWidget(btn_start)
        right.addWidget(btn_stop)
        right.addWidget(btn_reset_timer)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Өлчөө жана эсептөөлөр</b>"))
        self.input_tfinal = QLineEdit(); self.input_tfinal.setPlaceholderText("t акыркы (°C) — сиздин жоопуңуз")
        self.input_Q = QLineEdit(); self.input_Q.setPlaceholderText("Q суу (Дж) — сиздин эсептөөңүз")
        self.input_A = QLineEdit(); self.input_A.setPlaceholderText("A ток (Дж) — сиздин эсептөөңүз")
        self.input_eta = QLineEdit(); self.input_eta.setPlaceholderText("η — сиздин эсептөөңүз (0..1)")
        right.addWidget(self.input_tfinal)
        right.addWidget(self.input_Q)
        right.addWidget(self.input_A)
        right.addWidget(self.input_eta)

        btn_measure = QPushButton("Приборлорду өлчөө")
        btn_measure.clicked.connect(self.measure)
        btn_check = QPushButton("Эсептөөлөрдү текшерүү")
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

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.elapsed = 0.0
        self.heating = False
        self.heat_transfer_eff = 0.85

        self.random_experiment()

    def apply_params(self):
        try:
            U = float(self.input_U.text())
            R = float(self.input_R.text())
            m = float(self.input_m.text())
            t0 = float(self.input_t0.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "U, R, m, t баштапкысын киргизиңиз.")
            return
        I = U / R if R > 1e-9 else 0.0
        P = U * I
        self.voltmeter.set_value(U, vmax=max(1.0, U))
        self.ammeter.set_value(I, vmax=max(0.01, I*1.5))
        self.cal.set_params(m, t0)
        self.cal.set_power(P)
        self.lbl_result.setText("Параметрлер колдонулду. Спиралды иштетүү үчүн баскычты басыңыз.")
        self.elapsed = 0.0
        self.lbl_time.setText("t = 0.00 с")

    def start_heating(self):
        if self.cal.spiral_power <= 0:
            QMessageBox.information(self, "Инфо", "Адегечү параметрлерди колдонуңуз (U жана R) жана чынча чогултуңуз.")
            return
        if not self.heating:
            self.timer.start(200)
            self.heating = True
            self.lbl_result.setText("Спираль иштетүүлүп жатат. Нагрев жүрүүдө.")

    def stop_heating(self):
        if self.heating:
            self.timer.stop()
            self.heating = False
            self.lbl_result.setText("Спираль өчүрүлдү.")

    def reset_timer(self):
        self.elapsed = 0.0
        self.lbl_time.setText("t = 0.00 с")
        self.lbl_result.setText("Таймер сброшен.")

    def _tick(self):
        dt = 0.2
        self.elapsed += dt
        self.lbl_time.setText(f"t = {self.elapsed:.2f} с")
        self.cal.heat_step(dt, efficiency=self.heat_transfer_eff)

    def measure(self):
        t_meas = self.cal.t_current
        self.input_tfinal.setText(f"{t_meas:.2f}")
        U = self.voltmeter.value
        I = self.ammeter.value
        A = U * I * self.elapsed
        Q = C_WATER * self.cal.m_water * (self.cal.t_current - self.cal.t_initial)
        self.input_Q.setText(f"{Q:.2f}")
        self.input_A.setText(f"{A:.2f}")
        eta = Q / A if A > 1e-9 else 0.0
        self.input_eta.setText(f"{eta:.3f}")
        self.lbl_result.setText("Өлчөөлөр жана эсептөөлөр толтурулду (имитация).")

    def check_answers(self):
        try:
            t_user = float(self.input_tfinal.text())
            Q_user = float(self.input_Q.text())
            A_user = float(self.input_A.text())
            eta_user = float(self.input_eta.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "t, Q, A жана η үчүн сандык маанилерди киргизиңиз.")
            return
        t_true = self.cal.t_current
        Q_true = C_WATER * self.cal.m_water * (t_true - self.cal.t_initial)
        U = self.voltmeter.value
        I = self.ammeter.value
        A_true = U * I * self.elapsed
        eta_true = Q_true / A_true if A_true > 1e-9 else 0.0

        tol_t = 0.5
        tol_Q = max(0.03 * abs(Q_true), 0.5)
        tol_A = max(0.03 * abs(A_true), 0.5)
        tol_eta = max(0.05 * abs(eta_true), 0.02)

        lines = []
        lines.append("Текшерүүнүн жыйынтыгы:")
        lines.append("✅ t" if abs(t_user - t_true) <= tol_t else f"❌ t (туура {t_true:.2f} °C)")
        lines.append("✅ Q" if abs(Q_user - Q_true) <= tol_Q else f"❌ Q (туура {Q_true:.2f} Дж)")
        lines.append("✅ A" if abs(A_user - A_true) <= tol_A else f"❌ A (туура {A_true:.2f} Дж)")
        lines.append("✅ η" if abs(eta_user - eta_true) <= tol_eta else f"❌ η (туура {eta_true:.3f})")
        self.lbl_result.setText("\n".join(lines))

    def show_answers(self):
        t_true = self.cal.t_current
        Q_true = C_WATER * self.cal.m_water * (t_true - self.cal.t_initial)
        U = self.voltmeter.value
        I = self.ammeter.value
        A_true = U * I * self.elapsed
        eta_true = Q_true / A_true if A_true > 1e-9 else 0.0
        self.input_tfinal.setText(f"{t_true:.2f}")
        self.input_Q.setText(f"{Q_true:.2f}")
        self.input_A.setText(f"{A_true:.2f}")
        self.input_eta.setText(f"{eta_true:.3f}")
        self.lbl_result.setText("Туура маанилер көрсөтүлдү (модель боюнча).")

    def random_experiment(self):
        U = random.choice([3.0, 4.5, 6.0, 9.0, 12.0])
        R = random.uniform(2.0, 40.0)
        m = random.randint(100, 500)
        t0 = random.randint(15, 30)
        self.input_U.setText(f"{U:.1f}")
        self.input_R.setText(f"{R:.2f}")
        self.input_m.setText(f"{m:.0f}")
        self.input_t0.setText(f"{t0:.0f}")
        I = U / R if R > 1e-9 else 0.0
        P = U * I
        self.voltmeter.set_value(U, vmax=max(1.0, U))
        self.ammeter.set_value(I, vmax=max(0.01, I*1.5))
        self.cal.set_params(m, t0)
        self.cal.set_power(P)
        self.elapsed = 0.0
        self.lbl_time.setText("t = 0.00 с")
        self.input_tfinal.clear(); self.input_Q.clear(); self.input_A.clear(); self.input_eta.clear()
        self.lbl_result.setText("Кездейсоқ таажрыйба түзүлдү.")

    def reset_all(self):
        self.input_U.clear(); self.input_R.clear(); self.input_m.clear(); self.input_t0.clear()
        self.input_tfinal.clear(); self.input_Q.clear(); self.input_A.clear(); self.input_eta.clear()
        self.cal.set_params(200.0, 20.0)
        self.cal.set_power(0.0)
        self.voltmeter.set_value(0.0, vmax=5.0)
        self.ammeter.set_value(0.0, vmax=1.0)
        self.elapsed = 0.0
        self.lbl_time.setText("t = 0.00 с")
        self.lbl_result.setText("Сброшено.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabHeaterApp()
    win.show()
    sys.exit(app.exec())
