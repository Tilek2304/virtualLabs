# lab_pendulum_g.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer, QPointF

class PendulumWidget(QFrame):
    """
    Маятник анимациясы жана өлчөө.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 420)
        # Параметрлер
        self.l_m = 1.0            # узундук (м)
        self.px_per_m = 300.0     # масштаб
        self.l_px = self.l_m * self.px_per_m
        self.theta = 0.25         # бурч (рад)
        self.omega = 0.0
        self.g_model = 9.81
        self.damping = 0.02
        self.dt = 0.016
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(int(self.dt*1000))
        # Өлчөө
        self.measure_running = False
        self.crossings = []
        self.last_sign = None

    def set_params(self, l_m=None, theta_deg=None, g_model=None, damping=None):
        if l_m is not None:
            self.l_m = float(l_m)
            self.l_px = self.l_m * self.px_per_m
        if theta_deg is not None:
            self.theta = math.radians(float(theta_deg))
        if g_model is not None:
            self.g_model = float(g_model)
        if damping is not None:
            self.damping = float(damping)
        self.omega = 0.0
        self.crossings = []
        self.last_sign = None
        self.update()

    def start_measure(self):
        self.measure_running = True
        self.crossings = []
        self.last_sign = math.copysign(1.0, math.sin(self.theta)) if abs(self.theta)>1e-6 else 1.0

    def stop_measure(self):
        self.measure_running = False

    def reset_motion(self):
        self.theta = 0.25
        self.omega = 0.0
        self.crossings = []
        self.last_sign = None
        self.update()

    def _tick(self):
        # theta'' = - (g / l) * sin(theta) - damping * omega
        alpha = - (self.g_model / self.l_m) * math.sin(self.theta) - self.damping * self.omega
        self.omega += alpha * self.dt
        self.theta += self.omega * self.dt
        
        if self.measure_running:
            sign = math.copysign(1.0, self.theta) if abs(self.theta)>1e-6 else 0.0
            if self.last_sign is not None and sign != 0.0 and sign != self.last_sign:
                self.crossings.append(self._current_time())
            self.last_sign = sign
        self.update()

    def _current_time(self):
        import time
        return time.time()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))
        cx, cy = w//2, 80
        
        # Бекиткич
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(160,160,160))
        p.drawRect(cx-40, cy-8, 80, 12)
        
        # Жип жана жүк
        x = cx + int(self.l_px * math.sin(self.theta))
        y = cy + int(self.l_px * math.cos(self.theta))
        p.setPen(QPen(QColor(80,80,120), 3))
        p.drawLine(cx, cy+6, x, y)
        p.setBrush(QColor(200,60,60)); p.setPen(QPen(Qt.black,2))
        p.drawEllipse(x-18, y-18, 36, 36)
        
        # Текст
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",10))
        p.drawText(12, 18, f"l = {self.l_m:.3f} м ({int(self.l_px)} px)")
        p.drawText(12, 36, f"θ = {math.degrees(self.theta):.2f}°  ω = {self.omega:.3f} рад/с")
        # КОТОРМО: g (модель)
        p.drawText(12, 54, f"g (модель) = {self.g_model:.4f} м/с²")
        
        if len(self.crossings) >= 2:
            times = self.crossings
            periods = []
            for i in range(len(times)-2):
                try:
                    pval = times[i+2] - times[i]
                    if pval>0:
                        periods.append(pval)
                except:
                    pass
            if periods:
                avgT = sum(periods)/len(periods)
                # КОТОРМО: Акыркы T... (орточо)
                p.drawText(12, 72, f"Акыркы T ≈ {avgT:.3f} с ({len(periods)} маани боюнча орточо)")

class LabPendulumApp(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Маятник и g -> Маятник жана g (эркин түшүү ылдамдануусун өлчөө)
        self.setWindowTitle("Лабораториялык иш — Маятник жана g (эркин түшүү ылдамдануусун өлчөө)")
        self.setMinimumSize(1100, 700)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.pend = PendulumWidget()
        left.addWidget(self.pend)

        # Правая панель
        # КОТОРМО: Заголовок
        right.addWidget(QLabel("<b>Маятниктин параметрлери</b>"))
        
        self.input_l = QLineEdit(); self.input_l.setPlaceholderText("мисалы 1.00")
        self.input_theta = QLineEdit(); self.input_theta.setPlaceholderText("мисалы 14")
        self.input_gmodel = QLineEdit(); self.input_gmodel.setPlaceholderText("мисалы 9.81")
        
        right.addWidget(QLabel("Узундук l (м)"))
        right.addWidget(self.input_l)
        right.addWidget(QLabel("Баштапкы бурч θ (°)"))
        right.addWidget(self.input_theta)
        right.addWidget(QLabel("g модели (м/с²) — милдеттүү эмес"))
        right.addWidget(self.input_gmodel)

        right.addSpacing(6)
        # КОТОРМО: Измерения -> Өлчөөлөр
        right.addWidget(QLabel("<b>Өлчөөлөр</b>"))
        self.chk_manual = QCheckBox("Кол менен жазуу (авто толтуруу жок)")
        right.addWidget(self.chk_manual)
        
        self.input_n = QLineEdit(); self.input_n.setPlaceholderText("мисалы 10")
        right.addWidget(QLabel("Термелүү саны (n)"))
        right.addWidget(self.input_n)

        right.addSpacing(6)
        # КОТОРМО: Окуучунун жооптору
        right.addWidget(QLabel("<b>Окуучунун жооптору</b>"))
        self.input_T = QLineEdit(); self.input_T.setPlaceholderText("T (с) — мезгил")
        self.input_g_user = QLineEdit(); self.input_g_user.setPlaceholderText("g (м/с²) — сиздин эсептөө")
        
        right.addWidget(self.input_T)
        right.addWidget(self.input_g_user)

        # Кнопки
        # КОТОРМО: Применить -> Колдонуу
        btn_apply = QPushButton("Колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        # КОТОРМО: Запустить -> Баштоо
        btn_start = QPushButton("Баштоо")
        btn_start.clicked.connect(self.start_pendulum)
        # КОТОРМО: Остановить -> Токтотуу
        btn_stop = QPushButton("Токтотуу")
        btn_stop.clicked.connect(self.stop_pendulum)
        # КОТОРМО: Сброс движения -> Кыймылды тазалоо
        btn_reset = QPushButton("Кыймылды тазалоо")
        btn_reset.clicked.connect(self.reset_motion)
        # КОТОРМО: Измерить -> Өлчөө
        btn_measure = QPushButton("Өлчөө")
        btn_measure.clicked.connect(self.measure)
        # КОТОРМО: Проверить g -> g текшерүү
        btn_check = QPushButton("g текшерүү")
        btn_check.clicked.connect(self.check)
        # КОТОРМО: Показать ответ -> Жоопту көрсөтүү
        btn_show = QPushButton("Жоопту көрсөтүү")
        btn_show.clicked.connect(self.show_answer)
        # КОТОРМО: Случайный -> Кокустан тандалган
        btn_random = QPushButton("Кокустан тандалган тажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        # КОТОРМО: Сброс всех полей -> Талааларды тазалоо
        btn_clear = QPushButton("Талааларды тазалоо")
        btn_clear.clicked.connect(self.clear_fields)

        right.addWidget(btn_apply)
        right.addWidget(btn_start)
        right.addWidget(btn_stop)
        right.addWidget(btn_reset)
        right.addWidget(btn_measure)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_clear)

        right.addSpacing(8)
        # КОТОРМО: Результаты -> Жыйынтыктар
        right.addWidget(QLabel("<b>Жыйынтыктар</b>"))
        self.lbl_info = QLabel("Инструкция: l маанисин коюп, маятникти иштетиңиз, T мезгилин өлчөңүз.")
        self.lbl_info.setWordWrap(True)
        right.addWidget(self.lbl_info)
        right.addStretch(1)

        self.random_experiment()
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(200)

    def apply_params(self):
        try:
            l = float(self.input_l.text()) if self.input_l.text().strip() else self.pend.l_m
            theta = float(self.input_theta.text()) if self.input_theta.text().strip() else math.degrees(self.pend.theta)
            gmodel = float(self.input_gmodel.text()) if self.input_gmodel.text().strip() else self.pend.g_model
        except Exception:
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "l, θ жана g үчүн сан маанилерин киргизиңиз.")
            return
        self.pend.set_params(l_m=l, theta_deg=theta, g_model=gmodel)
        # КОТОРМО: Параметры применены -> Параметрлер колдонулду
        self.lbl_info.setText("Параметрлер колдонулду. «Баштоо» баскычын басыңыз.")
        self._update_ui()

    def start_pendulum(self):
        if not self.chk_manual.isChecked():
            self.pend.start_measure()
        # КОТОРМО: Маятник запущен -> Маятник иштеди
        self.lbl_info.setText("Маятник иштеди.")
        self._update_ui()

    def stop_pendulum(self):
        self.pend.stop_measure()
        # КОТОРМО: Маятник остановлен -> Маятник токтоду
        self.lbl_info.setText("Маятник токтоду.")
        self._update_ui()

    def reset_motion(self):
        self.pend.reset_motion()
        # КОТОРМО: Движение сброшено -> Кыймыл башынан башталды
        self.lbl_info.setText("Кыймыл башынан башталды.")
        self._update_ui()

    def measure(self):
        if self.chk_manual.isChecked():
            self.lbl_info.setText("Кол режими: T талаасы автоматтык толтурулбайт.")
            return
        try:
            n = int(self.input_n.text()) if self.input_n.text().strip() else 10
        except Exception:
            n = 10
        T0 = 2 * math.pi * math.sqrt(self.pend.l_m / self.pend.g_model)
        total_time = n * T0 * (1 + random.uniform(-0.01, 0.01))
        T_meas = total_time / n
        self.input_T.setText(f"{T_meas:.4f}")
        # КОТОРМО: Измерение... -> Өлчөө (имитация):
        self.lbl_info.setText(f"Өлчөө (имитация): {n} термелүү убактысы ≈ {total_time:.3f} с, T ≈ {T_meas:.4f} с.")
        self._update_ui()

    def check(self):
        try:
            T_user = float(self.input_T.text())
            g_user = float(self.input_g_user.text())
            l = float(self.input_l.text()) if self.input_l.text().strip() else self.pend.l_m
        except Exception:
            QMessageBox.warning(self, "Ката", "T, g жана l маанилерин киргизиңиз.")
            return
        if T_user <= 0:
            QMessageBox.information(self, "Маалымат", "T оң сан болушу керек.")
            return
        g_calc = 4 * math.pi**2 * l / (T_user**2)
        g_true = self.pend.g_model
        tol_calc = max(0.03 * abs(g_calc), 0.01)
        tol_true = max(0.05 * abs(g_true), 0.05)
        ok_user = abs(g_user - g_calc) <= tol_calc
        ok_model = abs(g_calc - g_true) <= tol_true
        lines = []
        if ok_user:
            lines.append("✅ Сиздин g эсебиңиз туура.")
        else:
            lines.append(f"❌ Сиздин g эсебиңиз ката. g_эсеп = {g_calc:.4f} м/с².")
        if ok_model:
            lines.append("✅ Чыныгы мааниге жакын.")
        else:
            lines.append(f"❌ Чыныгы мааниден айырмаланат: g = {g_true:.4f} м/с² ( piela ±{tol_true:.2f}).")
        self.lbl_info.setText("\n".join(lines))

    def show_answer(self):
        T0 = 2 * math.pi * math.sqrt(self.pend.l_m / self.pend.g_model)
        self.input_T.setText(f"{T0:.4f}")
        g_calc = 4 * math.pi**2 * self.pend.l_m / (T0**2)
        self.input_g_user.setText(f"{g_calc:.4f}")
        self.lbl_info.setText("Туура маанилер көрсөтүлдү.")
        self._update_ui()

    def random_experiment(self):
        l = random.uniform(0.2, 2.0)
        theta = random.uniform(5.0, 18.0)
        gmodel = random.uniform(9.78, 9.83)
        self.input_l.setText(f"{l:.3f}")
        self.input_theta.setText(f"{theta:.1f}")
        self.input_gmodel.setText(f"{gmodel:.3f}")
        self.pend.set_params(l_m=l, theta_deg=theta, g_model=gmodel)
        self.input_T.clear(); self.input_g_user.clear(); self.input_n.clear()
        self.lbl_info.setText("Жаңы тажрыйба даярдалды. «Баштоо», анан «Өлчөө» баскычын басыңыз.")
        self._update_ui()

    def clear_fields(self):
        self.input_T.clear(); self.input_g_user.clear()
        self.lbl_info.setText("Тазаланды.")
        self._update_ui()

    def _update_ui(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabPendulumApp()
    win.show()
    sys.exit(app.exec())