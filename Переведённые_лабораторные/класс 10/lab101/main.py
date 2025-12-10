# lab_em_induction.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer

# --- Вспомогательные функции ---
def flux_change(L, dI=0.0, dB=0.0, area=1.0):
    return L * dB * area

# --- Универсальный аналоговый прибор (гальванометр / вольтметр) ---
class MeterWidget(QFrame):
    def __init__(self, kind="μA", parent=None):
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
            frac = max(-1.0, min(1.0, self.value / self.max_display))
        ang = -60 + (frac + 1) * 60
        r = math.radians(ang)
        p.setPen(QPen(QColor(200,30,30),2))
        p.drawLine(cx, cy, cx + int((R-14)*math.cos(r)), cy - int((R-14)*math.sin(r)))
        p.setPen(QPen(Qt.black,2)); p.setFont(QFont("Sans",12,QFont.Bold))
        p.drawText(cx-12, cy+6, self.kind)
        p.setFont(QFont("Sans",9))
        if abs(self.value) < 1e-6:
            val_text = "0.00"
        else:
            val_text = f"{self.value:.3g}"
        p.drawText(8, h-10, val_text)

# --- Виджет: катушка + движущийся магнит + анимация ---
class InductionWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(760, 420)
        # модельные параметры
        self.N = 200            # число витков (условно)
        self.area = 0.01        # площадь витка (м^2) — условная единица
        self.B0 = 0.8           # индукция магнита (Т) при центре
        self.magnet_x = -200.0  # положение магнита по x относительно центра (px)
        self.magnet_speed = 0.0 # скорость движения магнита (px/s)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(30)
        # для вычисления ΔΦ/Δt
        self.prev_flux = self._flux_at(self.magnet_x)
        self.prev_time = 0.0
        self.elapsed = 0.0
        # подключённая нагрузка (в модели влияет на ток)
        self.R_load = 100.0

        # гальванометр: текущее индуцированное напряжение и ток
        self.E_ind = 0.0
        self.I_ind = 0.0

    def set_params(self, N=None, area=None, B0=None, R_load=None):
        if N is not None: self.N = int(N)
        if area is not None: self.area = float(area)
        if B0 is not None: self.B0 = float(B0)
        if R_load is not None: self.R_load = float(R_load)
        # сброс предыдущих значений
        self.prev_flux = self._flux_at(self.magnet_x)
        self.prev_time = 0.0
        self.elapsed = 0.0
        self.update()

    def _flux_at(self, x_px):
        # простая модель: B в центре катушки зависит от расстояния до магнита
        # перевод px -> метры: 100 px = 0.05 m (условно)
        px_to_m = 0.0005
        x_m = x_px * px_to_m
        # модель поля: B(x) = B0 * exp(- (x_m / d0)^2 )
        d0 = 0.03
        B = self.B0 * math.exp(- (x_m / d0)**2)
        # поток Φ = N * B * A
        return self.N * B * self.area

    def _tick(self):
        dt = 0.03
        self.elapsed += dt
        # обновляем положение магнита
        self.magnet_x += self.magnet_speed * dt
        # ограничим движение в пределах видимой области
        if self.magnet_x < -320: self.magnet_x = -320; self.magnet_speed = 0.0
        if self.magnet_x > 320: self.magnet_x = 320; self.magnet_speed = 0.0
        # вычисляем поток и ЭДС
        flux = self._flux_at(self.magnet_x)
        dflux = flux - self.prev_flux
        E = 0.0
        if abs(dt) > 1e-9:
            E = - dflux / dt  # В (модель)
        # индуцированный ток через нагрузку
        I_ind = E / self.R_load if abs(self.R_load) > 1e-9 else 0.0
        self.E_ind = E
        self.I_ind = I_ind
        # сохраняем для следующего шага
        self.prev_flux = flux
        self.prev_time += dt
        self.update()

    def set_magnet_speed(self, speed_px_per_s):
        self.magnet_speed = float(speed_px_per_s)

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))
        cx = w // 2
        baseline = h // 2

        # рисуем катушку (вид спереди)
        coil_w = 220; coil_h = 160
        coil_x = cx - coil_w//2; coil_y = baseline - coil_h//2
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(230,230,240))
        p.drawRoundedRect(coil_x, coil_y, coil_w, coil_h, 8, 8)
        # витки (горизонтальные дуги)
        p.setPen(QPen(QColor(120,60,20), 2))
        turns = min(30, max(6, self.N // 8))
        for i in range(turns):
            t = i / max(1, turns-1)
            y = coil_y + 8 + t * (coil_h - 16)
            p.drawArc(coil_x + 8, int(y)-8, coil_w - 16, 16, 0, 180*16)

        # рисуем магнит (прямоугольник с полюсами) — положение зависит от self.magnet_x
        mag_cx = cx + int(self.magnet_x)
        mag_cy = baseline
        mag_w = 80; mag_h = 60
        # левый полюс N (красный), правый S (синий)
        p.setPen(QPen(Qt.black,1))
        p.setBrush(QColor(220,60,60))
        p.drawRect(mag_cx - mag_w//2, mag_cy - mag_h//2, mag_w//2, mag_h)
        p.setBrush(QColor(60,60,220))
        p.drawRect(mag_cx, mag_cy - mag_h//2, mag_w//2, mag_h)
        p.setPen(QPen(Qt.white,1)); p.setFont(QFont("Sans",9,QFont.Bold))
        p.drawText(mag_cx - mag_w//2 + 8, mag_cy - 6, "N")
        p.drawText(mag_cx + 8, mag_cy - 6, "S")

        # стрелки поля (условная индикация направления)
        p.setPen(QPen(QColor(80,80,80,120), 1))
        for i in range(-3,4):
            x = mag_cx + i*18
            p.drawLine(x, mag_cy - 26, x, mag_cy - 10)
            p.drawLine(x, mag_cy + 26, x, mag_cy + 10)

        # подписи и цифровые значения
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",10))
        p.drawText(12, 18, f"N витков (модель) = {self.N}")
        p.drawText(12, 36, f"Площадь витка A = {self.area:.4f} m^2")
        p.drawText(12, 54, f"B0 (модель) = {self.B0:.3f} T")
        # поток и ЭДС
        flux = self.prev_flux
        p.drawText(12, 72, f"Φ (модель) = {flux:.6e} Wb")
        p.drawText(12, 90, f"ЭДС (модель) = {self.E_ind:.6e} V")
        p.drawText(12, 108, f"I_ind (модель) = {self.I_ind:.6e} A (через R={self.R_load:.1f} Ω)")

# --- Главное приложение и логика проверки ---
class LabInductionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык — Электромагниттик индукция катушка + магнит")
        self.setMinimumSize(1100, 700)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        # виджет индукции
        self.ind_widget = InductionWidget()
        left.addWidget(self.ind_widget)

        # приборы: гальванометр (μA)
        meters = QHBoxLayout()
        self.galvanometer = MeterWidget("μA")
        meters.addWidget(self.galvanometer)
        left.addLayout(meters)

        # правая панель: параметры и поля ученика
        right.addWidget(QLabel("<b>Таажрыйба параметрлери</b>"))
        right.addWidget(QLabel("Виток саны N"))
        self.input_N = QLineEdit(); self.input_N.setPlaceholderText("мисалы 200")
        right.addWidget(self.input_N)
        right.addWidget(QLabel("Витко аймагы A (m^2)"))
        self.input_A = QLineEdit(); self.input_A.setPlaceholderText("мисалы 0.01")
        right.addWidget(self.input_A)
        right.addWidget(QLabel("Магниттин индукциясы B0 (T)"))
        self.input_B0 = QLineEdit(); self.input_B0.setPlaceholderText("мисалы 0.8")
        right.addWidget(self.input_B0)
        right.addWidget(QLabel("Жүктөмөнүн сопротивления R (Ω)"))
        self.input_R = QLineEdit(); self.input_R.setPlaceholderText("мисалы 100")
        right.addWidget(self.input_R)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Магниттин кыймалдуу</b>"))
        right.addWidget(QLabel("Магниттин кыймал ылдамдыгы (px/s)"))
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setRange(-800, 800)
        self.slider_speed.setValue(0)
        self.slider_speed.valueChanged.connect(self.on_speed_change)
        right.addWidget(self.slider_speed)
        self.lbl_speed = QLabel("v = 0 px/s")
        right.addWidget(self.lbl_speed)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Режим</b>"))
        self.chk_manual = QCheckBox("Кол менен режим (окуучу өзү өлчөөнү жазды)")
        right.addWidget(self.chk_manual)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Окуучунун өлчөө талаалары</b>"))
        self.input_dphi = QLineEdit(); self.input_dphi.setPlaceholderText("ΔΦ (Wb) — потокту өзгөрүшү")
        self.input_dt = QLineEdit(); self.input_dt.setPlaceholderText("Δt (s) — убакыт өзгөрүшү")
        self.input_E = QLineEdit(); self.input_E.setPlaceholderText("ЭДС E (V) — сиздин эсептөөңүз")
        right.addWidget(self.input_dphi)
        right.addWidget(self.input_dt)
        right.addWidget(self.input_E)

        # кнопки
        btn_apply = QPushButton("Параметрлерди колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        btn_start = QPushButton("Кыймалдуу баштоо")
        btn_start.clicked.connect(self.start_motion)
        btn_stop = QPushButton("Токтоо")
        btn_stop.clicked.connect(self.stop_motion)
        btn_measure = QPushButton("Өлчөө (имитация)")
        btn_measure.clicked.connect(self.measure)
        btn_check = QPushButton("E текшерүү")
        btn_check.clicked.connect(self.check)
        btn_show = QPushButton("Жоопту көрсөтүү")
        btn_show.clicked.connect(self.show_answer)
        btn_random = QPushButton("Кездейсоқ таажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        btn_reset = QPushButton("Сброс")
        btn_reset.clicked.connect(self.reset_all)

        right.addWidget(btn_apply)
        right.addWidget(btn_start)
        right.addWidget(btn_stop)
        right.addWidget(btn_measure)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        right.addSpacing(8)
        right.addWidget(QLabel("<b>Жыйынтыктар жана кеңештер</b>"))
        self.lbl_flux = QLabel("Φ: — Wb")
        self.lbl_E = QLabel("E (модель): — V")
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setWordWrap(True)
        right.addWidget(self.lbl_flux)
        right.addWidget(self.lbl_E)
        right.addWidget(self.lbl_feedback)
        right.addStretch(1)

        # стартовые параметры
        self.random_experiment()
        # таймер для обновления UI (галванометр)
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(150)

    def on_speed_change(self, val):
        self.lbl_speed.setText(f"v = {val} px/s")
        self.ind_widget.set_magnet_speed(val)

    def apply_params(self):
        try:
            N = int(self.input_N.text()) if self.input_N.text().strip() else self.ind_widget.N
            A = float(self.input_A.text()) if self.input_A.text().strip() else self.ind_widget.area
            B0 = float(self.input_B0.text()) if self.input_B0.text().strip() else self.ind_widget.B0
            R = float(self.input_R.text()) if self.input_R.text().strip() else self.ind_widget.R_load
        except Exception:
            QMessageBox.warning(self, "Ката", "N, A, B0 жана R үчүн сандык маанилерди киргизиңиз.")
            return
        self.ind_widget.set_params(N=N, area=A, B0=B0, R_load=R)
        self.lbl_feedback.setText("Параметрлер колдонулду. «Кыймалдуу баштоо» же «Өлчөө» басыңыз.")
        self._update_ui()

    def start_motion(self):
        # движение уже управляется слайдером; просто даём пользователю знать
        self.lbl_feedback.setText("Магниттин кыймалдуусу идет (ылдамдыгын өтчүк менен чалуу).")
        # не меняем скорость здесь

    def stop_motion(self):
        self.ind_widget.set_magnet_speed(0.0)
        self.slider_speed.setValue(0)
        self.lbl_feedback.setText("Кыймалдуу токтоду.")
        self._update_ui()

    def measure(self):
        # автоматическое заполнение полей (если не ручной режим)
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Кол менен режим: талаалар автоматтык толтурулбайт.")
            self._update_ui()
            return
        # имитация измерения: используем модельные значения с шумом
        # ΔΦ за последний шаг — аппроксимация: используем E_ind и dt
        E = self.ind_widget.E_ind
        # возьмём Δt как 0.03 (шаг модели) или пользовательский ввод
        dt = 0.03
        # ΔΦ = -E * Δt
        dphi = - E * dt
        # добавим шум
        dphi_meas = dphi * (1 + random.uniform(-0.02, 0.02))
        dt_meas = dt * (1 + random.uniform(-0.01, 0.01))
        E_meas = E * (1 + random.uniform(-0.03, 0.03))
        self.input_dphi.setText(f"{dphi_meas:.6e}")
        self.input_dt.setText(f"{dt_meas:.4f}")
        self.input_E.setText(f"{E_meas:.6e}")
        self.lbl_feedback.setText("Талаалар имитация өлчөөлөрү менен толтурулду (бир аз катасы бар).")
        self._update_ui()

    def check(self):
        try:
            dphi_user = float(self.input_dphi.text())
            dt_user = float(self.input_dt.text())
            E_user = float(self.input_E.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "ΔΦ, Δt жана сиздин E эсептөөңүз үчүн сандык маанилерди киргизиңиз.")
            return
        if abs(dt_user) < 1e-9:
            QMessageBox.information(self, "Билүү", "Δt эсептөө үчүн өтө кичине.")
            return
        E_calc = - dphi_user / dt_user
        E_model = self.ind_widget.E_ind
        tol_calc = max(0.03 * abs(E_calc) if abs(E_calc)>1e-9 else 1e-6, 1e-6)
        tol_model = max(0.05 * abs(E_model) if abs(E_model)>1e-9 else 1e-6, 1e-6)
        ok_user = abs(E_user - E_calc) <= tol_calc
        ok_model = abs(E_calc - E_model) <= tol_model
        lines = []
        if ok_user:
            lines.append("✅ Сиздин E эсептөөңүз өлчөөлөр боюнча эсептөөгө дал келет.")
        else:
            lines.append(f"❌ Сиздин E өлчөөлөр менен эсептелген E менен дал келбейт. E_эсептөө = {E_calc:.6e} V.")
        if ok_model:
            lines.append("✅ Өлчөө модельдүү ЭДСге жакын (имитация боюнча).")
        else:
            lines.append(f"❌ Өлчөө модельдүү ЭДС менен айырмалуу = {E_model:.6e} V (сверх ±{tol_model:.6e}).")
        self.lbl_feedback.setText("\n".join(lines))
        self._update_ui()

    def show_answer(self):
        # показываем модельные значения (ΔΦ аппроксимируем через E*dt)
        E = self.ind_widget.E_ind
        dt = 0.03
        dphi = - E * dt
        self.input_dphi.setText(f"{dphi:.6e}")
        self.input_dt.setText(f"{dt:.4f}")
        self.input_E.setText(f"{E:.6e}")
        self.lbl_feedback.setText("Модель боюнча туура маанилер (шаг боюнча приближение).")
        self._update_ui()

    def random_experiment(self):
        N = random.choice([100, 200, 400])
        A = random.choice([0.005, 0.01, 0.02])
        B0 = random.uniform(0.4, 1.2)
        R = random.choice([50.0, 100.0, 200.0])
        self.input_N.setText(str(N))
        self.input_A.setText(f"{A:.4f}")
        self.input_B0.setText(f"{B0:.3f}")
        self.input_R.setText(f"{R:.1f}")
        self.ind_widget.set_params(N=N, area=A, B0=B0, R_load=R)
        # поставим магнит в левую позицию и дадим небольшую скорость вправо
        self.ind_widget.magnet_x = -260.0
        self.slider_speed.setValue(300)
        self.ind_widget.set_magnet_speed(300)
        self.input_dphi.clear(); self.input_dt.clear(); self.input_E.clear()
        self.lbl_feedback.setText("Кездейсоқ таажрыйба түзүлдү. «Өлчөө» басыңыз же ылдамдыгын чалуу.")
        self._update_ui()

    def reset_all(self):
        self.input_N.clear(); self.input_A.clear(); self.input_B0.clear(); self.input_R.clear()
        self.input_dphi.clear(); self.input_dt.clear(); self.input_E.clear()
        self.ind_widget.set_params(N=200, area=0.01, B0=0.8, R_load=100.0)
        self.ind_widget.magnet_x = -200.0
        self.ind_widget.set_magnet_speed(0.0)
        self.slider_speed.setValue(0)
        self.lbl_feedback.setText("Сброшено.")
        self._update_ui()

    def _update_ui(self):
        # обновляем подписи и прибор
        self.lbl_flux.setText(f"Φ (модель): {self.ind_widget.prev_flux:.6e} Wb")
        self.lbl_E.setText(f"E (модель): {self.ind_widget.E_ind:.6e} V")
        # гальванометр показывает I_ind в микроамперах для наглядности
        I_uA = self.ind_widget.I_ind * 1e6
        self.galvanometer.set_value(I_uA, vmax=max(1.0, abs(I_uA)*1.5))
        # подписи
        self.lbl_feedback.setText(self.lbl_feedback.text())  # оставляем текущее сообщение

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabInductionApp()
    win.show()
    sys.exit(app.exec())
