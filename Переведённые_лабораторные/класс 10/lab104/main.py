# lab_temp_coeff_copper.py
# Зарыйтуу: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer

G = 9.80665

# Универсальный аналоговый прибор (омметр / демонстрация)
class MeterWidget(QFrame):
    def __init__(self, kind="Ω", parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.kind = kind
        self.value = 0.0
        self.max_display = 1.0

    def set_value(self, val, vmax=None):
        self.value = val if val is not None else 0.0
        if vmax is not None:
            self.max_display = max(1e-9, float(vmax))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
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
        p.drawText(cx-12, cy+6, self.kind)
        p.setFont(QFont("Sans",9))
        if self.kind == "Ω":
            p.drawText(8, h-10, f"{self.value:.4f} {self.kind}")
        else:
            p.drawText(8, h-10, f"{self.value:.2f} {self.kind}")

# Виджет: калориметр с катушкой меди и нагревателем
class CalorimeterCopperWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(680, 380)
        # модельные параметры
        self.R0 = 5.0000            # сопротивление при T0 (Ом)
        self.T0 = 20.0              # начальная температура (°C)
        self.alpha_true = 0.0039    # температурный коэффициент меди (примерно 0.0039 1/°C)
        # динамика нагрева
        self.T = float(self.T0)
        self.heater_power = 0.5     # условная мощность нагревателя (Вт)
        self.heat_on = False
        self.heat_rate = 0.2        # °C / s при включенном нагреве (условно)
        self.cool_rate = 0.02       # °C / s при выключенном (охлаждение)
        # визуализация
        self.wave_phase = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(80)

    def set_params(self, R0=None, T0=None, alpha=None, heater_power=None):
        if R0 is not None: self.R0 = float(R0)
        if T0 is not None:
            self.T0 = float(T0)
            self.T = float(T0)
        if alpha is not None: self.alpha_true = float(alpha)
        if heater_power is not None: self.heater_power = float(heater_power)
        self.update()

    def start_heating(self):
        self.heat_on = True

    def stop_heating(self):
        self.heat_on = False

    def heat_step(self, dT):
        # мгновенное изменение температуры (например, внешнее воздействие)
        self.T += dT
        self.update()

    def _tick(self):
        # простая модель нагрева/охлаждения
        dt = 0.08
        if self.heat_on:
            # нагрев пропорционален мощности и уменьшается при росте T
            self.T += self.heat_rate * dt * (1.0 + 0.02 * (self.heater_power - 0.5))
        else:
            # охлаждение к окружающей температуре T0
            self.T -= self.cool_rate * dt * (self.T - self.T0)
        self.wave_phase += 0.12
        if self.wave_phase > 2*math.pi:
            self.wave_phase -= 2*math.pi
        self.update()

    def resistance_at_T(self, T=None):
        if T is None: T = self.T
        return self.R0 * (1 + self.alpha_true * (T - self.T0))

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))

        cx = w // 3
        top = 30
        # корпус калориметра
        tube_w = 160; tube_h = 260
        tube_x = cx - tube_w//2; tube_y = top + 10
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(240,240,245))
        p.drawRoundedRect(tube_x, tube_y, tube_w, tube_h, 8, 8)

        # катушка меди внутри (спираль)
        coil_cx = cx
        coil_cy = tube_y + tube_h//2
        p.setPen(QPen(QColor(150,80,30), 3))
        turns = 8
        r0 = 18
        for i in range(turns):
            r = r0 + i*6
            p.drawArc(int(coil_cx - r), int(coil_cy - r), int(2*r), int(2*r), 0, 360*16)

        # нагреватель снизу (плитка)
        heater_x = cx + tube_w//2 + 60
        heater_y = tube_y + tube_h - 40
        p.setPen(QPen(Qt.black,1)); p.setBrush(QColor(220,120,80) if self.heat_on else QColor(200,200,200))
        p.drawRect(heater_x - 30, heater_y - 10, 60, 20)
        p.setFont(QFont("Sans",9)); p.setPen(QPen(Qt.black,1))
        p.drawText(heater_x - 18, heater_y + 6, "Heater")

        # термометр справа (столбик)
        therm_x = cx + tube_w//2 + 20
        therm_y = top + 10
        therm_h = tube_h - 20
        p.setPen(QPen(Qt.black,1)); p.setBrush(QColor(255,255,255))
        p.drawRoundedRect(therm_x, therm_y, 36, therm_h, 6, 6)
        # столбик
        minT, maxT = -10.0, 120.0
        frac = (self.T - minT) / (maxT - minT)
        frac = max(0.0, min(1.0, frac))
        fill_h = int(frac * (therm_h - 20))
        p.setBrush(QColor(220,40,40))
        p.drawRect(therm_x + 8, therm_y + therm_h - 10 - fill_h, 20, fill_h)
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",9))
        p.drawText(therm_x - 6, therm_y + therm_h + 14, f"{self.T:.2f} °C")

        # подписи
        R_now = self.resistance_at_T()
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",10))
        p.drawText(12, 18, f"T0 = {self.T0:.2f} °C, R0 = {self.R0:.4f} Ω")
        p.drawText(12, 36, f"T = {self.T:.2f} °C")
        p.drawText(12, 54, f"R(T) = {R_now:.4f} Ω")
        p.drawText(12, 72, f"α (модель) = {self.alpha_true:.6f} 1/°C")
        p.drawText(12, 90, f"Heater: {'ON' if self.heat_on else 'OFF'}, P ≈ {self.heater_power:.2f} arb")

# Главное приложение: измерение температурного коэффициента меди
class LabTempCoeffCopperApp(QWidget):
    """
    Лабораторная: α = ΔR / (R0 * Δt) для меди.
    Интерфейс: калориметр + катушка меди + омметр + нагреватель.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Медянын температуралык коэффициенти — α = ΔR / (R0·Δt)")
        self.setMinimumSize(1100, 700)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        # виджет калориметра
        self.cal_widget = CalorimeterCopperWidget()
        left.addWidget(self.cal_widget)

        # приборы: омметр
        meters = QHBoxLayout()
        self.ohmmeter = MeterWidget("Ω")
        meters.addWidget(self.ohmmeter)
        left.addLayout(meters)

        # правая панель: параметры и поля ученика
        right.addWidget(QLabel("<b>Эксперименттин параметрлери</b>"))
        self.input_R0 = QLineEdit(); self.input_R0.setPlaceholderText("R0 (Ω) — сопротивление при T0")
        self.input_T0 = QLineEdit(); self.input_T0.setPlaceholderText("T0 (°C) — начальная температура")
        self.input_alpha = QLineEdit(); self.input_alpha.setPlaceholderText("α (1/°C) — (опционально для модели)")
        self.input_heater = QLineEdit(); self.input_heater.setPlaceholderText("Мощность нагревателя (условно)")
        right.addWidget(self.input_R0)
        right.addWidget(self.input_T0)
        right.addWidget(self.input_alpha)
        right.addWidget(self.input_heater)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Ысытууну башкаруу</b>"))
        btn_heat_on = QPushButton("Ысытууну күйгүзүү")
        btn_heat_on.clicked.connect(self.heat_on)
        btn_heat_off = QPushButton("Ысытууну өчүрүү")
        btn_heat_off.clicked.connect(self.heat_off)
        btn_step = QPushButton("Тез кадам ысытуу +ΔT")
        btn_step.clicked.connect(self.quick_heat)
        right.addWidget(btn_heat_on); right.addWidget(btn_heat_off); right.addWidget(btn_step)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Режим</b>"))
        self.chk_manual = QCheckBox("Кол режими (студент өзү көрсөтүүлөрдү жазып алат)")
        right.addWidget(self.chk_manual)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Студенттин талаалары (өлчөөлөрдү киргизиңиз)</b>"))
        self.input_Rt = QLineEdit(); self.input_Rt.setPlaceholderText("R_t (Ω) — сопротивление при T")
        self.input_Tt = QLineEdit(); self.input_Tt.setPlaceholderText("T (°C) — конечная температура")
        self.input_alpha_user = QLineEdit(); self.input_alpha_user.setPlaceholderText("α — ваш расчёт")
        right.addWidget(self.input_Rt)
        right.addWidget(self.input_Tt)
        right.addWidget(self.input_alpha_user)

        # кнопки
        btn_apply = QPushButton("Параметрлерди колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        btn_measure = QPushButton("Өлчөө (имитация)")
        btn_measure.clicked.connect(self.measure)
        btn_check = QPushButton("α текшер")
        btn_check.clicked.connect(self.check)
        btn_show = QPushButton("Жоопту көрсөт")
        btn_show.clicked.connect(self.show_answer)
        btn_random = QPushButton("Кокус эксперимент")
        btn_random.clicked.connect(self.random_experiment)
        btn_reset = QPushButton("Сброс")
        btn_reset.clicked.connect(self.reset_all)

        right.addWidget(btn_apply)
        right.addWidget(btn_measure)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        right.addSpacing(8)
        right.addWidget(QLabel("<b>Жыйынтыктар жана кеңештер</b>"))
        self.lbl_Rnow = QLabel("R(t): — Ω")
        self.lbl_Tnow = QLabel("T: — °C")
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setWordWrap(True)
        right.addWidget(self.lbl_Rnow)
        right.addWidget(self.lbl_Tnow)
        right.addWidget(self.lbl_feedback)
        right.addStretch(1)

        # стартовые значения
        self.random_experiment()
        # таймер для обновления прибора
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_meter)
        self.ui_timer.start(200)

    def _update_meter(self):
        R_now = self.cal_widget.resistance_at_T()
        self.ohmmeter.set_value(R_now, vmax=max(0.1, R_now*1.5))
        self.lbl_Rnow.setText(f"R(t): {R_now:.4f} Ω")
        self.lbl_Tnow.setText(f"T: {self.cal_widget.T:.2f} °C")

    def apply_params(self):
        try:
            R0 = float(self.input_R0.text()) if self.input_R0.text().strip() else self.cal_widget.R0
            T0 = float(self.input_T0.text()) if self.input_T0.text().strip() else self.cal_widget.T0
            alpha = float(self.input_alpha.text()) if self.input_alpha.text().strip() else self.cal_widget.alpha_true
            heater = float(self.input_heater.text()) if self.input_heater.text().strip() else self.cal_widget.heater_power
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения R0, T0, α и мощность нагревателя.")
            return
        self.cal_widget.set_params(R0=R0, T0=T0, alpha=alpha, heater_power=heater)
        self.input_Rt.clear(); self.input_Tt.clear(); self.input_alpha_user.clear()
        self.lbl_feedback.setText("Параметры применены. Включите нагрев или используйте быстрый шаг.")
        self._update_meter()

    def heat_on(self):
        self.cal_widget.start_heating()
        self.lbl_feedback.setText("Нагрев включён.")
        self._update_meter()

    def heat_off(self):
        self.cal_widget.stop_heating()
        self.lbl_feedback.setText("Нагрев выключён.")
        self._update_meter()

    def quick_heat(self):
        # быстрый шаг нагрева: + (1..8) °C
        dT = random.uniform(1.0, 8.0)
        self.cal_widget.heat_step(dT)
        self.lbl_feedback.setText(f"Быстрый шаг: температура увеличена на ≈{dT:.2f} °C.")
        self._update_meter()

    def measure(self):
        # автоматическое заполнение полей (если не ручной режим)
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Ручной режим: поля не заполняются автоматически.")
            self._update_meter()
            return
        R_t = self.cal_widget.resistance_at_T()
        T_t = self.cal_widget.T
        # добавим небольшую погрешность имитации
        R_meas = R_t * (1 + random.uniform(-0.01, 0.01))
        T_meas = T_t * (1 + random.uniform(-0.003, 0.003))
        self.input_Rt.setText(f"{R_meas:.4f}")
        self.input_Tt.setText(f"{T_meas:.2f}")
        self.lbl_feedback.setText("Поля заполнены имитацией измерений (с небольшой погрешностью).")
        self._update_meter()

    def check(self):
        try:
            R0 = float(self.input_R0.text()) if self.input_R0.text().strip() else self.cal_widget.R0
            T0 = float(self.input_T0.text()) if self.input_T0.text().strip() else self.cal_widget.T0
            R_t = float(self.input_Rt.text())
            T_t = float(self.input_Tt.text())
            alpha_user = float(self.input_alpha_user.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения R0, T0, R_t, T и ваш расчёт α.")
            return
        deltaT = T_t - T0
        if abs(deltaT) < 1e-6:
            QMessageBox.information(self, "Инфо", "ΔT слишком мал для корректного расчёта α.")
            return
        alpha_calc = (R_t - R0) / (R0 * deltaT)
        alpha_true = self.cal_widget.alpha_true
        tol_calc = max(0.03 * abs(alpha_calc), 1e-5)
        tol_true = max(0.05 * abs(alpha_true), 1e-5)
        ok_user_calc = abs(alpha_user - alpha_calc) <= tol_calc
        ok_vs_true = abs(alpha_calc - alpha_true) <= tol_true
        lines = []
        if ok_user_calc:
            lines.append("✅ Ваш расчёт α соответствует вычислению по измерениям.")
        else:
            lines.append(f"❌ Ваш α не совпадает с расчётом по измерениям. α_расчёт = {alpha_calc:.6f} 1/°C.")
        if ok_vs_true:
            lines.append("✅ Измерение близко к модельному значению α (по заданной модели).")
        else:
            lines.append(f"❌ Измерение отличается от модельного α = {alpha_true:.6f} (допуск ±{tol_true:.6f}).")
        self.lbl_feedback.setText("\n".join(lines))

    def show_answer(self):
        R0 = self.cal_widget.R0
        T0 = self.cal_widget.T0
        R_t = self.cal_widget.resistance_at_T()
        T_t = self.cal_widget.T
        deltaT = T_t - T0
        if abs(deltaT) < 1e-9:
            QMessageBox.information(self, "Инфо", "ΔT слишком мал или не задан.")
            return
        alpha_calc = (R_t - R0) / (R0 * deltaT)
        self.input_Rt.setText(f"{R_t:.4f}")
        self.input_Tt.setText(f"{T_t:.2f}")
        self.input_alpha_user.setText(f"{alpha_calc:.6f}")
        self.lbl_feedback.setText("Показаны правильные значения по модели.")
        self._update_meter()

    def random_experiment(self):
        # генерируем случайные параметры: R0 0.5..20 Ом, T0 15..25, alpha около меди 0.0035..0.0042
        R0 = random.uniform(0.5, 20.0)
        T0 = random.uniform(15.0, 25.0)
        alpha = random.uniform(0.0035, 0.0042)
        heater = random.uniform(0.3, 1.2)
        self.input_R0.setText(f"{R0:.4f}")
        self.input_T0.setText(f"{T0:.2f}")
        self.input_alpha.setText(f"{alpha:.6f}")
        self.input_heater.setText(f"{heater:.2f}")
        self.cal_widget.set_params(R0=R0, T0=T0, alpha=alpha, heater_power=heater)
        # небольшой нагрев для практики
        self.cal_widget.heat_step(random.uniform(1.0, 8.0))
        self.input_Rt.clear(); self.input_Tt.clear(); self.input_alpha_user.clear()
        self.lbl_feedback.setText("Случайный эксперимент сгенерирован. Нажмите «Измерить» или включите нагрев.")
        self._update_meter()

    def reset_all(self):
        self.input_R0.clear(); self.input_T0.clear(); self.input_alpha.clear(); self.input_heater.clear()
        self.input_Rt.clear(); self.input_Tt.clear(); self.input_alpha_user.clear()
        self.cal_widget.set_params(R0=5.0, T0=20.0, alpha=0.0039, heater_power=0.5)
        self.cal_widget.T = self.cal_widget.T0
        self.cal_widget.stop_heating()
        self.lbl_feedback.setText("Сброшено.")
        self._update_meter()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabTempCoeffCopperApp()
    win.show()
    sys.exit(app.exec())
