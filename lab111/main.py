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
    """Анимированный маятник: длина l (px), угол theta, трение, визуализация."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 420)
        # физические параметры (модельные)
        self.l_m = 1.0            # длина в метрах (для расчёта g)
        self.px_per_m = 300.0     # масштаб: метры -> пиксели
        self.l_px = self.l_m * self.px_per_m
        self.theta = 0.25         # начальный угол (рад)
        self.omega = 0.0
        self.g_model = 9.81
        self.damping = 0.02
        # симуляция времени
        self.dt = 0.016
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(int(self.dt*1000))
        # счётчик колебаний и измерение периода
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
        # простая численная интеграция (симпл. Эйлер/Верле)
        # уравнение: theta'' = - (g / l) * sin(theta) - damping * omega
        alpha = - (self.g_model / self.l_m) * math.sin(self.theta) - self.damping * self.omega
        self.omega += alpha * self.dt
        self.theta += self.omega * self.dt
        # измерение пересечений нуля для периода (фиксируем моменты, когда theta меняет знак и проходит через 0 с положительной производной)
        if self.measure_running:
            sign = math.copysign(1.0, self.theta) if abs(self.theta)>1e-6 else 0.0
            # detect zero crossing from negative to positive or positive to negative
            if self.last_sign is not None and sign != 0.0 and sign != self.last_sign:
                # записываем время (в секундах) — используем внутренний счётчик шагов
                t = len(self.crossings) * 0.0  # placeholder, we'll store timestamps externally
                # Instead of relying on internal time, we append a timestamp using QTimer elapsed approximation:
                # We'll store Python time via incremental counter
                # For simplicity, store step index (we'll convert outside)
                self.crossings.append(self._current_time())
            self.last_sign = sign
        self.update()

    def _current_time(self):
        # approximate time using number of ticks since start: use QTimer interval and count
        # store as monotonic count of ticks
        # We'll use Python's time module for accurate timestamps
        import time
        return time.time()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))
        cx, cy = w//2, 80
        # опора
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(160,160,160))
        p.drawRect(cx-40, cy-8, 80, 12)
        # нить и груз
        x = cx + int(self.l_px * math.sin(self.theta))
        y = cy + int(self.l_px * math.cos(self.theta))
        p.setPen(QPen(QColor(80,80,120), 3))
        p.drawLine(cx, cy+6, x, y)
        p.setBrush(QColor(200,60,60)); p.setPen(QPen(Qt.black,2))
        p.drawEllipse(x-18, y-18, 36, 36)
        # подписи
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",10))
        p.drawText(12, 18, f"l = {self.l_m:.3f} m ({int(self.l_px)} px)")
        p.drawText(12, 36, f"θ = {math.degrees(self.theta):.2f}°  ω = {self.omega:.3f} rad/s")
        p.drawText(12, 54, f"g (модель) = {self.g_model:.4f} m/s²")
        # если измерения есть — показываем последние периоды
        if len(self.crossings) >= 2:
            # compute periods between every two consecutive same-direction crossings (i.e., two zero-crossings correspond to half period)
            # better: detect times of same sign crossing separated by two crossings -> full period
            times = self.crossings
            # compute differences between every second crossing to get approximate period
            periods = []
            for i in range(len(times)-2):
                # full period approx = times[i+2] - times[i]
                try:
                    pval = times[i+2] - times[i]
                    if pval>0:
                        periods.append(pval)
                except:
                    pass
            if periods:
                avgT = sum(periods)/len(periods)
                p.drawText(12, 72, f"Последний T ≈ {avgT:.3f} s (среднее по {len(periods)} значениям)")

class LabPendulumApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Маятник и g — измерение ускорения свободного падения")
        self.setMinimumSize(1100, 700)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        # виджет маятника
        self.pend = PendulumWidget()
        left.addWidget(self.pend)

        # правая панель: параметры и поля ученика
        right.addWidget(QLabel("<b>Параметры маятника</b>"))
        right.addWidget(QLabel("Длина l (m)"))
        self.input_l = QLineEdit(); self.input_l.setPlaceholderText("например 1.00")
        right.addWidget(self.input_l)
        right.addWidget(QLabel("Начальный угол θ (°)"))
        self.input_theta = QLineEdit(); self.input_theta.setPlaceholderText("например 14")
        right.addWidget(self.input_theta)
        right.addWidget(QLabel("Модель g (m/s²) — опционально"))
        self.input_gmodel = QLineEdit(); self.input_gmodel.setPlaceholderText("например 9.81")
        right.addWidget(self.input_gmodel)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Измерения</b>"))
        self.chk_manual = QCheckBox("Ручной режим (ученик сам записывает времена)")
        right.addWidget(self.chk_manual)
        right.addWidget(QLabel("Число колебаний для измерения (n)"))
        self.input_n = QLineEdit(); self.input_n.setPlaceholderText("например 10")
        right.addWidget(self.input_n)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Поля ученика (введите свои измерения)</b>"))
        self.input_T = QLineEdit(); self.input_T.setPlaceholderText("T (s) — период (или среднее время n колебаний / n)")
        self.input_g_user = QLineEdit(); self.input_g_user.setPlaceholderText("g (m/s²) — ваш расчёт")
        right.addWidget(self.input_T)
        right.addWidget(self.input_g_user)

        # кнопки
        btn_apply = QPushButton("Применить параметры")
        btn_apply.clicked.connect(self.apply_params)
        btn_start = QPushButton("Запустить маятник")
        btn_start.clicked.connect(self.start_pendulum)
        btn_stop = QPushButton("Остановить маятник")
        btn_stop.clicked.connect(self.stop_pendulum)
        btn_reset = QPushButton("Сброс движения")
        btn_reset.clicked.connect(self.reset_motion)
        btn_measure = QPushButton("Измерить (имитация времени)")
        btn_measure.clicked.connect(self.measure)
        btn_check = QPushButton("Проверить g")
        btn_check.clicked.connect(self.check)
        btn_show = QPushButton("Показать ответ")
        btn_show.clicked.connect(self.show_answer)
        btn_random = QPushButton("Случайный эксперимент")
        btn_random.clicked.connect(self.random_experiment)
        btn_clear = QPushButton("Сброс всех полей")
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
        right.addWidget(QLabel("<b>Результаты и подсказки</b>"))
        self.lbl_info = QLabel("Инструкция: задайте l, запустите маятник, измерьте период T (или время n колебаний).")
        self.lbl_info.setWordWrap(True)
        right.addWidget(self.lbl_info)
        right.addStretch(1)

        self.random_experiment()
        # таймер для обновления UI (показывать модельные значения)
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(200)

    def apply_params(self):
        try:
            l = float(self.input_l.text()) if self.input_l.text().strip() else self.pend.l_m
            theta = float(self.input_theta.text()) if self.input_theta.text().strip() else math.degrees(self.pend.theta)
            gmodel = float(self.input_gmodel.text()) if self.input_gmodel.text().strip() else self.pend.g_model
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения l, θ и (опционально) g.")
            return
        self.pend.set_params(l_m=l, theta_deg=theta, g_model=gmodel)
        self.lbl_info.setText("Параметры применены. Нажмите «Запустить маятник» и затем «Измерить» или введите свои времена.")
        self._update_ui()

    def start_pendulum(self):
        # просто продолжаем таймер в виджете (он уже работает); включаем измерение пересечений если нужно
        if not self.chk_manual.isChecked():
            # если автоматический режим — начинаем измерение пересечений
            self.pend.start_measure()
        self.lbl_info.setText("Маятник запущен. В автоматическом режиме собираются пересечения для оценки периода.")
        self._update_ui()

    def stop_pendulum(self):
        self.pend.stop_measure()
        self.lbl_info.setText("Маятник остановлен (измерение приостановлено).")
        self._update_ui()

    def reset_motion(self):
        self.pend.reset_motion()
        self.lbl_info.setText("Движение сброшено.")
        self._update_ui()

    def measure(self):
        # автоматическое заполнение поля T: в модели вычислим период малых колебаний T0 = 2π sqrt(l/g)
        if self.chk_manual.isChecked():
            self.lbl_info.setText("Ручной режим: поле T не заполняется автоматически.")
            return
        try:
            n = int(self.input_n.text()) if self.input_n.text().strip() else 10
        except Exception:
            n = 10
        # модельный период (малые углы)
        T0 = 2 * math.pi * math.sqrt(self.pend.l_m / self.pend.g_model)
        # имитация: измерим время n колебаний = n * T0 with noise
        total_time = n * T0 * (1 + random.uniform(-0.01, 0.01))
        T_meas = total_time / n
        self.input_T.setText(f"{T_meas:.4f}")
        self.lbl_info.setText(f"Измерение (имитация): время {n} колебаний ≈ {total_time:.3f} s, T ≈ {T_meas:.4f} s.")
        self._update_ui()

    def check(self):
        try:
            T_user = float(self.input_T.text())
            g_user = float(self.input_g_user.text())
            l = float(self.input_l.text()) if self.input_l.text().strip() else self.pend.l_m
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения T, g и l.")
            return
        if T_user <= 0:
            QMessageBox.information(self, "Инфо", "T должно быть положительным.")
            return
        g_calc = 4 * math.pi**2 * l / (T_user**2)
        g_true = self.pend.g_model
        tol_calc = max(0.03 * abs(g_calc), 0.01)
        tol_true = max(0.05 * abs(g_true), 0.05)
        ok_user = abs(g_user - g_calc) <= tol_calc
        ok_model = abs(g_calc - g_true) <= tol_true
        lines = []
        if ok_user:
            lines.append("✅ Ваш расчёт g соответствует вычислению по измерениям.")
        else:
            lines.append(f"❌ Ваш g не совпадает с расчётом по измерениям. g_расчёт = {g_calc:.4f} m/s².")
        if ok_model:
            lines.append("✅ Измерение близко к модельному g (по симуляции).")
        else:
            lines.append(f"❌ Измерение отличается от модельного g = {g_true:.4f} m/s² (допуск ±{tol_true:.2f}).")
        self.lbl_info.setText("\n".join(lines))

    def show_answer(self):
        # показываем модельный период и рассчитанное g
        T0 = 2 * math.pi * math.sqrt(self.pend.l_m / self.pend.g_model)
        self.input_T.setText(f"{T0:.4f}")
        g_calc = 4 * math.pi**2 * self.pend.l_m / (T0**2)
        self.input_g_user.setText(f"{g_calc:.4f}")
        self.lbl_info.setText("Показаны правильные значения по модели (малые углы).")
        self._update_ui()

    def random_experiment(self):
        # генерируем случайную длину 0.2..2.0 m, угол 5..20 deg, модель g 9.7..9.83
        l = random.uniform(0.2, 2.0)
        theta = random.uniform(5.0, 18.0)
        gmodel = random.uniform(9.78, 9.83)
        self.input_l.setText(f"{l:.3f}")
        self.input_theta.setText(f"{theta:.1f}")
        self.input_gmodel.setText(f"{gmodel:.3f}")
        self.pend.set_params(l_m=l, theta_deg=theta, g_model=gmodel)
        self.input_T.clear(); self.input_g_user.clear(); self.input_n.clear()
        self.lbl_info.setText("Случайный эксперимент сгенерирован. Нажмите «Запустить маятник» и затем «Измерить».")
        self._update_ui()

    def clear_fields(self):
        self.input_T.clear(); self.input_g_user.clear()
        self.lbl_info.setText("Поля очищены.")
        self._update_ui()

    def _update_ui(self):
        # обновление подписи (период и т.д.) происходит в виджете маятника
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabPendulumApp()
    win.show()
    sys.exit(app.exec())
