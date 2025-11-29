# lab_motor_model.py
# Требуется: pip install PySide6
import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QRadialGradient, QPolygonF
)
from PySide6.QtCore import Qt, QTimer, QPointF

class MeterWidget(QFrame):
    """Универсальный аналоговый прибор (A/V) со шкалой и стрелкой."""
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
        cx, cy = w//2, h//2
        R = min(w, h)//2 - 8
        p.fillRect(self.rect(), QColor(250,250,250))
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(255,255,255))
        p.drawEllipse(cx - R, cy - R, 2*R, 2*R)
        p.setPen(QPen(Qt.black,1))
        for ang in range(-60, 61, 10):
            r = math.radians(ang)
            p.drawLine(cx + int((R-8)*math.cos(r)), cy - int((R-8)*math.sin(r)),
                       cx + int(R*math.cos(r)),       cy - int(R*math.sin(r)))
        frac = 0.0
        if self.max_display > 0:
            frac = max(0.0, min(1.0, abs(self.value) / self.max_display))
        ang = -60 + frac*120.0
        r = math.radians(ang)
        p.setPen(QPen(QColor(200,30,30),2))
        p.drawLine(cx, cy, cx + int((R-14)*math.cos(r)), cy - int((R-14)*math.sin(r)))
        p.setPen(QPen(Qt.black,2)); p.setFont(QFont("Sans",12,QFont.Bold))
        p.drawText(cx-8, cy+6, self.kind)
        p.setFont(QFont("Sans",9))
        p.drawText(8, h-10, f"{self.value:.2f} {self.kind}")

class MotorWidget(QFrame):
    """
    Улучшенная визуальная модель электродвигателя с реальной анимацией ротора.
    Модель момента с учётом коммутатора: M ~ sign * k * N * I * B * |sin(theta)|.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 420)
        # параметры модели
        self.I = 0.0
        self.U = 6.0
        self.N_turns = 50
        self.B = 1.0
        self.reverse = False
        # динамика
        self.theta = 0.0     # угол, рад
        self.omega = 0.0     # угловая скорость, рад/с
        self.alpha = 0.0
        self.J = 1.0
        self.damp = 0.22
        # счётчик оборотов
        self.rev_count = 0
        self.last_theta = 0.0
        # таймер для плавной анимации (~60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def set_params(self, I=None, U=None, N=None, B=None, reverse=None):
        if I is not None: self.I = float(I)
        if U is not None: self.U = float(U)
        if N is not None: self.N_turns = int(N)
        if B is not None: self.B = float(B)
        if reverse is not None: self.reverse = bool(reverse)
        self.update()

    def reset_motion(self):
        self.theta = 0.0
        self.omega = 0.0
        self.rev_count = 0
        self.last_theta = 0.0
        self.update()

    def invert_direction_immediately(self):
        # при мгновенной смене полярности инвертируем ω, чтобы визуально сменить направление
        self.omega = -self.omega
        self.update()

    def _tick(self):
        # момент: используем абсолютное значение синуса, чтобы моделировать действие коммутатора
        k = 0.08
        sign = -1.0 if self.reverse else 1.0
        # M всегда направлен в сторону выбранной полярности, величина ~ |sin(theta)|
        M = sign * k * self.N_turns * self.I * self.B * abs(math.sin(self.theta))
        # уравнение вращения: J*alpha = M - damp*omega
        self.alpha = (M - self.damp * self.omega) / self.J
        dt = 0.016
        # semi-implicit Euler для устойчивости
        self.omega += self.alpha * dt
        # ограничение максимальной скорости для стабильности и визуальной читаемости
        max_omega = 60.0  # рад/с
        if self.omega > max_omega: self.omega = max_omega
        if self.omega < -max_omega: self.omega = -max_omega
        self.theta += self.omega * dt

        # подсчёт оборотов (корректно при больших ω)
        two_pi = 2 * math.pi
        cur = (self.theta % two_pi)
        prev = (self.last_theta % two_pi)
        if prev > 5.5 and cur < 0.5:
            self.rev_count += 1
        self.last_theta = self.theta

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(246,248,250))
        cx, cy = w//2, h//2
        R_stator = 130
        R_rotor  = 90

        # фон
        grad = QRadialGradient(cx, cy, max(R_stator, R_rotor) + 80, cx, cy)
        grad.setColorAt(0.0, QColor(255,255,255))
        grad.setColorAt(1.0, QColor(235,240,245))
        p.setBrush(grad); p.setPen(Qt.NoPen)
        p.drawRect(0,0,w,h)

        # статор: дуги N и S
        p.setPen(QPen(Qt.black,2))
        p.setBrush(QColor(220,60,60))
        p.drawPie(cx - R_stator, cy - R_stator, 2*R_stator, 2*R_stator, 30*16, 120*16)
        p.setFont(QFont("Sans",12,QFont.Bold)); p.setPen(QPen(Qt.white,1))
        p.drawText(cx - 22, cy - R_stator + 40, "N")
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(60,60,220))
        p.drawPie(cx - R_stator, cy - R_stator, 2*R_stator, 2*R_stator, 210*16, 120*16)
        p.setPen(QPen(Qt.white,1)); p.drawText(cx - 22, cy + R_stator - 20, "S")

        # ротор: рисуем повернутый элемент
        p.save()
        p.translate(cx, cy)
        p.rotate(math.degrees(self.theta))

        # диск ротора
        rotor_grad = QRadialGradient(0, 0, R_rotor, 0, 0)
        rotor_grad.setColorAt(0.0, QColor(235,235,240))
        rotor_grad.setColorAt(1.0, QColor(210,210,220))
        p.setBrush(rotor_grad)
        p.setPen(QPen(Qt.black,2))
        p.drawEllipse(-R_rotor, -R_rotor, 2*R_rotor, 2*R_rotor)

        # спицы ротора (визуализация смазывания при высокой скорости)
        spoke_count = 6
        blur_alpha = int(min(140, abs(self.omega) * 60))
        p.setPen(QPen(QColor(120,120,140, max(60, blur_alpha)), 4))
        for i in range(spoke_count):
            ang = i * (360 / spoke_count)
            r = math.radians(ang)
            x = (R_rotor - 12) * math.cos(r)
            y = (R_rotor - 12) * math.sin(r)
            p.drawLine(0, 0, int(x), int(y))

        # катушка на роторе
        coil_w, coil_h = 140, 26
        p.setBrush(QColor(245,205,130))
        p.setPen(QPen(Qt.black,2))
        p.drawRoundedRect(-coil_w//2, -coil_h//2, coil_w, coil_h, 8, 8)
        # выводы катушки
        p.setPen(QPen(QColor(220,40,40),4))
        p.drawLine(-coil_w//2, 0, -coil_w//2 - 20, 0)
        p.setPen(QPen(QColor(40,40,220),4))
        p.drawLine(coil_w//2, 0, coil_w//2 + 20, 0)

        # коммутатор (кольцо)
        comm_R_outer = R_rotor - 8
        comm_R_inner = R_rotor - 20
        p.setPen(QPen(Qt.black,2))
        p.setBrush(QColor(180,160,140))
        p.drawEllipse(-comm_R_outer, -comm_R_outer, 2*comm_R_outer, 2*comm_R_outer)
        p.setBrush(QColor(220,200,180))
        p.drawEllipse(-comm_R_inner, -comm_R_inner, 2*comm_R_inner, 2*comm_R_inner)
        # сегменты коммутатора
        p.setPen(QPen(QColor(120,90,70),2))
        for ang in range(0, 360, 30):
            r = math.radians(ang)
            x0 = comm_R_inner * math.cos(r); y0 = comm_R_inner * math.sin(r)
            x1 = comm_R_outer * math.cos(r); y1 = comm_R_outer * math.sin(r)
            p.drawLine(int(x0), int(y0), int(x1), int(y1))

        p.restore()

        # щётки (фиксированные)
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(60,60,60))
        p.drawRoundedRect(cx - comm_R_outer - 6, cy - 10, 16, 20, 4, 4)
        p.drawRoundedRect(cx + comm_R_outer - 10, cy - 10, 16, 20, 4, 4)
        # проводники щёток
        p.setPen(QPen(QColor(200,30,30),2))
        p.drawLine(cx - comm_R_outer - 6, cy, cx - comm_R_outer - 26, cy - 28)
        p.setPen(QPen(QColor(30,30,200),2))
        p.drawLine(cx + comm_R_outer + 6, cy, cx + comm_R_outer + 26, cy + 28)

        # ось ротора
        p.setBrush(QColor(150,150,160)); p.setPen(QPen(Qt.black,2))
        p.drawEllipse(cx-6, cy-6, 12, 12)

        # стрелка направления вращения (наконечник через QPolygonF)
        p.setPen(QPen(QColor(80,80,80),2)); p.setBrush(Qt.NoBrush)
        arrow_R = R_rotor + 30
        base_ang = -40 if self.omega >= 0 else 220
        arc_span = 60
        p.drawArc(cx - arrow_R, cy - arrow_R, 2*arrow_R, 2*arrow_R, base_ang*16, arc_span*16)
        tip_ang = base_ang + arc_span
        tr = math.radians(tip_ang)
        tx = cx + arrow_R * math.cos(tr)
        ty = cy - arrow_R * math.sin(tr)
        pt1 = QPointF(tx, ty)
        pt2 = QPointF(tx - 10*math.cos(tr) + 6*math.sin(tr), ty + 10*math.sin(tr) + 6*math.cos(tr))
        pt3 = QPointF(tx - 10*math.cos(tr) - 6*math.sin(tr), ty + 10*math.sin(tr) - 6*math.cos(tr))
        poly = QPolygonF([pt1, pt2, pt3])
        p.setBrush(QColor(80,80,80))
        p.drawPolygon(poly)

        # подписи и цифровые значения
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",10))
        direction = "по часовой" if self.omega < 0 else "против"
        rpm = abs(self.omega) * (60.0/(2*math.pi))
        p.drawText(20, 30, f"I = {self.I:.2f} A, U = {self.U:.1f} V, N = {self.N_turns}, B = {self.B:.1f}")
        p.drawText(20, 48, f"ω = {self.omega:.2f} рад/с ({rpm:.0f} об/мин), обороты = {self.rev_count}, направление: {direction}")
        p.drawText(20, 66, f"Полярность: {'обратная' if self.reverse else 'прямая'}")

class LabMotorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная — Модель электродвигателя (реальная анимация)")
        self.setMinimumSize(1100, 700)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.motor = MotorWidget()
        left.addWidget(self.motor)

        meters = QHBoxLayout()
        self.voltmeter = MeterWidget("V")
        self.ammeter  = MeterWidget("A")
        meters.addWidget(self.voltmeter)
        meters.addWidget(self.ammeter)
        left.addLayout(meters)

        right.addWidget(QLabel("<b>Модель электродвигателя</b>"))
        info = QLabel("Меняйте I, полярность, число витков и индукцию. Наблюдайте вращение ротора в реальном времени.")
        info.setWordWrap(True)
        right.addWidget(info)

        right.addWidget(QLabel("<b>Ток I</b>"))
        self.slider_I = QSlider(Qt.Horizontal); self.slider_I.setRange(0, 500); self.slider_I.setValue(120)
        self.slider_I.valueChanged.connect(self.on_slider_I); right.addWidget(self.slider_I)
        self.lbl_I = QLabel("I = 1.20 A"); right.addWidget(self.lbl_I)

        right.addWidget(QLabel("<b>Напряжение U</b>"))
        self.slider_U = QSlider(Qt.Horizontal); self.slider_U.setRange(0, 120); self.slider_U.setValue(60)
        self.slider_U.valueChanged.connect(self.on_slider_U); right.addWidget(self.slider_U)
        self.lbl_U = QLabel("U = 6.0 V"); right.addWidget(self.lbl_U)

        self.chk_reverse = QCheckBox("Обратить полярность")
        self.chk_reverse.stateChanged.connect(self.on_reverse_changed)
        right.addWidget(self.chk_reverse)

        right.addWidget(QLabel("<b>Число витков N</b>"))
        self.input_N = QLineEdit(); self.input_N.setPlaceholderText("например 50"); right.addWidget(self.input_N)

        right.addWidget(QLabel("<b>Индукция магнита B</b>"))
        self.input_B = QLineEdit(); self.input_B.setPlaceholderText("например 1.0"); right.addWidget(self.input_B)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Ответ ученика</b>"))
        self.input_dir = QLineEdit(); self.input_dir.setPlaceholderText("Направление: 'по часовой' или 'против'")
        self.input_rev = QLineEdit(); self.input_rev.setPlaceholderText("Обороты за эксперимент")
        right.addWidget(self.input_dir); right.addWidget(self.input_rev)

        btn_apply = QPushButton("Применить параметры"); btn_apply.clicked.connect(self.apply_params)
        btn_reset_motion = QPushButton("Сбросить вращение"); btn_reset_motion.clicked.connect(self.motor.reset_motion)
        btn_measure = QPushButton("Измерить"); btn_measure.clicked.connect(self.measure)
        btn_check = QPushButton("Проверить ответ"); btn_check.clicked.connect(self.check)
        btn_show = QPushButton("Показать правильные значения"); btn_show.clicked.connect(self.show_answer)
        btn_random = QPushButton("Случайный эксперимент"); btn_random.clicked.connect(self.random_experiment)
        btn_reset = QPushButton("Сброс"); btn_reset.clicked.connect(self.reset_all)

        right.addWidget(btn_apply); right.addWidget(btn_reset_motion)
        right.addWidget(btn_measure); right.addWidget(btn_check)
        right.addWidget(btn_show); right.addWidget(btn_random); right.addWidget(btn_reset)

        self.lbl_result = QLabel(""); right.addWidget(self.lbl_result); right.addStretch(1)
        self.random_experiment()

    def on_slider_I(self, val):
        I = val / 100.0
        self.lbl_I.setText(f"I = {I:.2f} A")
        # обновляем модель и амперметр в реальном времени
        self.motor.set_params(I=I)
        self.ammeter.set_value(I, vmax=max(0.5, I*1.5))

    def on_slider_U(self, val):
        U = val / 10.0
        self.lbl_U.setText(f"U = {U:.1f} V")
        self.voltmeter.set_value(U, vmax=max(1.0, U))
        # сохраняем U в модели для подписи
        self.motor.set_params(U=U)

    def on_reverse_changed(self, state):
        rev = (state == Qt.Checked)
        # применяем полярность и мгновенно инвертируем ω для визуального эффекта
        self.motor.set_params(reverse=rev)
        self.motor.invert_direction_immediately()
        self.lbl_result.setText("Полярность изменена.")

    def apply_params(self):
        try:
            I = self.slider_I.value()/100.0
            U = self.slider_U.value()/10.0
            N = int(self.input_N.text()) if self.input_N.text().strip() else 50
            B = float(self.input_B.text()) if self.input_B.text().strip() else 1.0
            reverse = self.chk_reverse.isChecked()
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Проверьте ввод I, U, N, B.")
            return
        self.motor.set_params(I=I, U=U, N=N, B=B, reverse=reverse)
        self.ammeter.set_value(I, vmax=max(0.5, I*1.5))
        self.voltmeter.set_value(U, vmax=max(1.0, U))
        self.lbl_result.setText("Параметры применены.")

    def measure(self):
        direction = "по часовой" if self.motor.omega < 0 else "против"
        revs = self.motor.rev_count
        QMessageBox.information(self, "Измерение", f"Направление: {direction}\nОбороты: {revs}")
        self.lbl_result.setText("Измерение выполнено.")

    def check(self):
        user_dir = self.input_dir.text().strip().lower()
        try:
            user_rev = int(self.input_rev.text().strip())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите целое число оборотов.")
            return
        correct_dir = "по часовой" if self.motor.omega < 0 else "против"
        correct_rev = self.motor.rev_count
        ok_dir = (user_dir == correct_dir)
        tol_rev = max(1, int(0.1 * max(1, correct_rev)))
        ok_rev = abs(user_rev - correct_rev) <= tol_rev
        msg = []
        msg.append("✅ Направление верное." if ok_dir else f"❌ Направление неверно. Правильно: {correct_dir}.")
        msg.append("✅ Обороты верно." if ok_rev else f"❌ Обороты неверно. Правильно: {correct_rev} (±{tol_rev}).")
        self.lbl_result.setText("\n".join(msg))

    def show_answer(self):
        correct_dir = "по часовой" if self.motor.omega < 0 else "против"
        correct_rev = self.motor.rev_count
        self.input_dir.setText(correct_dir)
        self.input_rev.setText(str(correct_rev))
        self.lbl_result.setText("Показаны правильные значения.")

    def random_experiment(self):
        I = random.uniform(0.6, 3.0)
        U = random.choice([3.0, 4.5, 6.0, 9.0, 12.0])
        N = random.choice([30, 50, 100, 150])
        B = random.uniform(0.6, 1.4)
        reverse = random.choice([False, True])
        self.slider_I.setValue(int(I*100))
        self.slider_U.setValue(int(U*10))
        self.input_N.setText(str(N))
        self.input_B.setText(f"{B:.2f}")
        self.chk_reverse.setChecked(reverse)
        self.apply_params()
        self.motor.reset_motion()
        self.input_dir.clear(); self.input_rev.clear()
        self.lbl_result.setText("Случайный эксперимент готов.")

    def reset_all(self):
        self.slider_I.setValue(120)
        self.slider_U.setValue(60)
        self.input_N.clear(); self.input_B.clear()
        self.chk_reverse.setChecked(False)
        self.apply_params()
        self.motor.reset_motion()
        self.input_dir.clear(); self.input_rev.clear()
        self.lbl_result.setText("Сброшено.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabMotorApp()
    win.show()
    sys.exit(app.exec())
