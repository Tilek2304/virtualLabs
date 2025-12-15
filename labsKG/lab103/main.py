# lab_surface_tension.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush
from PySide6.QtCore import Qt, QTimer

G = 9.80665  # м/с^2

# Универсалдуу аналогдук прибор (масса / убакыт)
class MeterWidget(QFrame):
    def __init__(self, kind="g", parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 100)
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
        p.drawText(8, h-10, f"{self.value:.3f}")

# Бюретка жана тамчы
class BuretteWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(760, 420)
        # Параметрлер
        self.sigma_true = 0.072  # Н/м
        self.d_nozzle = 2.0e-3   # д (м)
        self.flow_rate = 5e-8    # агым ылдамдыгы (кг/с)
        self.drop_mass = 0.0     # тамчынын массасы (кг)
        self.drop_attached = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(40)     # ~25 FPS
        self.last_detach_mass = None
        self.last_detach_d = None

    def set_params(self, sigma=None, d_nozzle=None, flow_rate=None):
        if sigma is not None: self.sigma_true = float(sigma)
        if d_nozzle is not None: self.d_nozzle = float(d_nozzle)
        if flow_rate is not None: self.flow_rate = float(flow_rate)
        self.drop_mass = 0.0
        self.drop_attached = True
        self.last_detach_mass = None
        self.last_detach_d = None
        self.update()

    def _tick(self):
        if self.drop_attached:
            dt = 0.04
            self.drop_mass += self.flow_rate * dt
            # Үзүлүү шарты: m*g >= π*d*σ
            threshold = math.pi * self.d_nozzle * self.sigma_true
            if self.drop_mass * G >= threshold:
                self.last_detach_mass = self.drop_mass
                self.last_detach_d = self.d_nozzle
                self.drop_attached = False
                self.drop_mass = 0.0
        self.update()

    def simulate_detach_once(self):
        # m_detach = (π d σ) / g
        m_detach = (math.pi * self.d_nozzle * self.sigma_true) / G
        m_detach *= (1 + random.uniform(-0.02, 0.02))
        self.last_detach_mass = m_detach
        self.last_detach_d = self.d_nozzle * (1 + random.uniform(-0.01, 0.01))
        self.drop_mass = 0.0
        self.drop_attached = True
        self.update()
        return self.last_detach_mass, self.last_detach_d

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))

        cx = w // 2
        top = 40
        # Бюретка
        tube_w = 120; tube_h = 260
        tube_x = cx - tube_w//2; tube_y = top + 10
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(240,240,250))
        p.drawRoundedRect(tube_x, tube_y, tube_w, tube_h, 8, 8)
        p.setPen(QPen(Qt.black,1))
        for i in range(0, 13):
            y = tube_y + 10 + i * (tube_h - 20) / 12
            p.drawLine(tube_x + tube_w - 6, int(y), tube_x + tube_w - 2, int(y))
        # КОТОРМО: Burette -> Бюретка
        p.setFont(QFont("Sans",9)); p.drawText(tube_x + 6, tube_y - 6, "Бюретка")

        # Сопло
        nozzle_x = cx
        nozzle_y = tube_y + tube_h + 6
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(200,200,200))
        p.drawRoundedRect(nozzle_x - 10, nozzle_y - 6, 20, 12, 4, 4)

        # Тамчы
        rho = 1000.0
        scale = 400.0
        if self.drop_attached:
            V = self.drop_mass / rho
            if V > 0:
                r_m = (3.0 * V / (4.0 * math.pi)) ** (1.0/3.0)
            else:
                r_m = 0.0005
            r_px = max(2.0, min(60.0, r_m * scale))
            p.setPen(QPen(Qt.black,1)); p.setBrush(QColor(120,180,240))
            p.drawEllipse(int(nozzle_x - r_px), int(nozzle_y), int(2*r_px), int(1.2*r_px))
            p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",9))
            p.drawText(12, 18, f"m (тамчы) = {self.drop_mass*1e6:.2f} мг")
        else:
            p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",9))
            # КОТОРМО: Капля оторвалась -> Тамчы үзүлдү
            p.drawText(12, 18, "Тамчы үзүлдү — кийинкиге даяр.")
            p.setPen(QPen(Qt.black,1)); p.setBrush(QColor(120,180,240))
            p.drawEllipse(int(nozzle_x - 6), int(nozzle_y + 18), 12, 12)

        # Текст
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",10))
        p.drawText(12, 36, f"σ (модель) = {self.sigma_true:.5f} Н/м")
        p.drawText(12, 54, f"d сопло = {self.d_nozzle*1e3:.2f} мм")
        p.drawText(12, 72, f"агым = {self.flow_rate*1e6:.3f} мг/с")

        if self.last_detach_mass is not None:
            p.drawText(12, 90, f"Акыркы үзүлгөн m = {self.last_detach_mass*1e6:.2f} мг, d = {self.last_detach_d*1e3:.2f} мм")

class LabSurfaceTensionApp(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Бетонное натяжение -> Суюктуктун беттик тартылуу коэффициентин аныктоо (σ = m·g / (π·d))
        self.setWindowTitle("Лабораториялык иш — Суюктуктун беттик тартылуу коэффициенти (σ = m·g / (π·d))")
        self.setMinimumSize(1100, 700)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.burette = BuretteWidget()
        left.addWidget(self.burette)

        meters = QHBoxLayout()
        self.mass_meter = MeterWidget("мг")
        self.time_meter = MeterWidget("с")
        meters.addWidget(self.mass_meter); meters.addWidget(self.time_meter)
        left.addLayout(meters)

        # Правая панель
        # КОТОРМО: Заголовок
        right.addWidget(QLabel("<b>Тажрыйбанын параметрлери</b>"))
        
        self.input_sigma = QLineEdit(); self.input_sigma.setPlaceholderText("мисалы 0.072")
        self.input_d_mm = QLineEdit(); self.input_d_mm.setPlaceholderText("мисалы 2.0")
        self.input_flow = QLineEdit(); self.input_flow.setPlaceholderText("мисалы 0.050")
        
        right.addWidget(QLabel("σ (модель) Н/м (милдеттүү эмес)"))
        right.addWidget(self.input_sigma)
        right.addWidget(QLabel("Соплонун диаметри d (мм)"))
        right.addWidget(self.input_d_mm)
        right.addWidget(QLabel("Агым ылдамдыгы (мг/с)"))
        right.addWidget(self.input_flow)

        right.addSpacing(6)
        # КОТОРМО: Режим -> Режим
        right.addWidget(QLabel("<b>Режим</b>"))
        self.chk_manual = QCheckBox("Кол менен жазуу (авто толтуруу жок)")
        right.addWidget(self.chk_manual)

        right.addSpacing(6)
        # КОТОРМО: Поля ученика -> Окуучунун эсептөөлөрү
        right.addWidget(QLabel("<b>Окуучунун эсептөөлөрү</b>"))
        self.input_m_meas = QLineEdit(); self.input_m_meas.setPlaceholderText("m (мг) — үзүлгөн тамчынын массасы")
        self.input_d_meas = QLineEdit(); self.input_d_meas.setPlaceholderText("d (мм) — соплонун диаметри")
        self.input_sigma_user = QLineEdit(); self.input_sigma_user.setPlaceholderText("σ (Н/м) — сиздин эсептөө")
        
        right.addWidget(self.input_m_meas)
        right.addWidget(self.input_d_meas)
        right.addWidget(self.input_sigma_user)

        # Кнопки
        # КОТОРМО: Применить -> Колдонуу
        btn_apply = QPushButton("Колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        # КОТОРМО: Симулировать рост -> Тамчынын өсүүсүн жана үзүлүүсүн симуляциялоо
        btn_simulate = QPushButton("Тамчынын үзүлүүсүн симуляциялоо")
        btn_simulate.clicked.connect(self.simulate_detach)
        # КОТОРМО: Измерить -> Өлчөө
        btn_measure = QPushButton("Өлчөө")
        btn_measure.clicked.connect(self.measure)
        # КОТОРМО: Проверить σ -> σ текшерүү
        btn_check = QPushButton("σ текшерүү")
        btn_check.clicked.connect(self.check)
        # КОТОРМО: Показать ответ -> Жоопту көрсөтүү
        btn_show = QPushButton("Жоопту көрсөтүү")
        btn_show.clicked.connect(self.show_answer)
        # КОТОРМО: Случайный -> Кокустан тандалган
        btn_random = QPushButton("Кокустан тандалган тажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        # КОТОРМО: Сброс -> Кайра баштоо
        btn_reset = QPushButton("Кайра баштоо")
        btn_reset.clicked.connect(self.reset_all)

        right.addWidget(btn_apply)
        right.addWidget(btn_simulate)
        right.addWidget(btn_measure)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        right.addSpacing(8)
        # КОТОРМО: Результаты -> Жыйынтыктар
        right.addWidget(QLabel("<b>Жыйынтыктар</b>"))
        self.lbl_model = QLabel("Модель: —")
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setWordWrap(True)
        right.addWidget(self.lbl_model)
        right.addWidget(self.lbl_feedback)
        right.addStretch(1)

        self.random_experiment()
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(150)

    def apply_params(self):
        try:
            sigma = float(self.input_sigma.text()) if self.input_sigma.text().strip() else self.burette.sigma_true
            d_mm = float(self.input_d_mm.text()) if self.input_d_mm.text().strip() else self.burette.d_nozzle*1e3
            flow_mg_s = float(self.input_flow.text()) if self.input_flow.text().strip() else self.burette.flow_rate*1e6
        except Exception:
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "σ, d жана агым үчүн сан маанилерин киргизиңиз.")
            return
        d_m = d_mm * 1e-3
        flow_kg_s = flow_mg_s * 1e-6
        self.burette.set_params(sigma=sigma, d_nozzle=d_m, flow_rate=flow_kg_s)
        # КОТОРМО: Параметры применены -> Параметрлер колдонулду
        self.lbl_feedback.setText("Параметрлер колдонулду. «Тамчынын үзүлүүсүн симуляциялоо» баскычын басыңыз.")
        self._update_ui()

    def simulate_detach(self):
        m_detach, d_detach = self.burette.simulate_detach_once()
        flow = self.burette.flow_rate
        t_est = m_detach / flow if flow > 1e-12 else 0.0
        self.mass_meter.set_value(m_detach*1e6, vmax=max(1.0, m_detach*1e6*2))
        self.time_meter.set_value(t_est, vmax=max(0.1, t_est*1.5))
        # КОТОРМО: Симуляция... -> Симуляция: тамчы үзүлдү. «Өлчөө» баскычын басыңыз.
        self.lbl_feedback.setText("Симуляция: тамчы үзүлдү. «Өлчөө» баскычын басыңыз.")
        self._update_ui()

    def measure(self):
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Кол режими: талаалар автоматтык толтурулбайт.")
            return
        if self.burette.last_detach_mass is None:
            m_detach, d_detach = self.burette.simulate_detach_once()
        else:
            m_detach = self.burette.last_detach_mass
            d_detach = self.burette.last_detach_d
        m_meas = m_detach * (1 + random.uniform(-0.02, 0.02))
        d_meas = d_detach * (1 + random.uniform(-0.01, 0.01))
        self.input_m_meas.setText(f"{m_meas*1e6:.2f}")
        self.input_d_meas.setText(f"{d_meas*1e3:.3f}")
        # КОТОРМО: Поля заполнены -> Көрсөткүчтөр жазылды (кичине ката менен).
        self.lbl_feedback.setText("Көрсөткүчтөр жазылды (кичине ката менен).")
        self._update_ui()

    def check(self):
        try:
            m_mg = float(self.input_m_meas.text())
            d_mm = float(self.input_d_meas.text())
            sigma_user = float(self.input_sigma_user.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "Бардык талааларды толтуруңуз.")
            return
        m = m_mg * 1e-6
        d = d_mm * 1e-3
        if d <= 0:
            QMessageBox.information(self, "Маалымат", "d оң сан болушу керек.")
            return
        sigma_calc = (m * G) / (math.pi * d)
        sigma_true = self.burette.sigma_true
        tol_calc = max(0.03 * abs(sigma_calc), 1e-4)
        tol_true = max(0.05 * abs(sigma_true), 1e-4)
        ok_user = abs(sigma_user - sigma_calc) <= tol_calc
        ok_model = abs(sigma_calc - sigma_true) <= tol_true
        lines = []
        if ok_user:
            lines.append("✅ Сиздин σ эсебиңиз туура.")
        else:
            lines.append(f"❌ Сиздин σ эсебиңиз ката. σ_эсеп = {sigma_calc:.6f} Н/м.")
        if ok_model:
            lines.append("✅ Чыныгы мааниге жакын.")
        else:
            lines.append(f"❌ Чыныгы мааниден айырмаланат: σ = {sigma_true:.6f} Н/м.")
        self.lbl_feedback.setText("\n".join(lines))
        self._update_ui()

    def show_answer(self):
        if self.burette.last_detach_mass is None:
            m_detach, d_detach = self.burette.simulate_detach_once()
        else:
            m_detach = self.burette.last_detach_mass
            d_detach = self.burette.last_detach_d
        sigma_calc = (m_detach * G) / (math.pi * d_detach)
        self.input_m_meas.setText(f"{m_detach*1e6:.2f}")
        self.input_d_meas.setText(f"{d_detach*1e3:.3f}")
        self.input_sigma_user.setText(f"{sigma_calc:.6f}")
        self.lbl_feedback.setText("Туура маанилер көрсөтүлдү.")
        self._update_ui()

    def random_experiment(self):
        sigma = random.uniform(0.02, 0.12)
        d_mm = random.uniform(1.0, 4.0)
        flow_mg_s = random.uniform(0.01, 0.2)
        self.input_sigma.setText(f"{sigma:.5f}")
        self.input_d_mm.setText(f"{d_mm:.3f}")
        self.input_flow.setText(f"{flow_mg_s:.3f}")
        self.apply_params()
        self.burette.simulate_detach_once()
        self.input_m_meas.clear(); self.input_d_meas.clear(); self.input_sigma_user.clear()
        self.lbl_feedback.setText("Жаңы тажрыйба даярдалды.")
        self._update_ui()

    def reset_all(self):
        self.input_sigma.clear(); self.input_d_mm.clear(); self.input_flow.clear()
        self.input_m_meas.clear(); self.input_d_meas.clear(); self.input_sigma_user.clear()
        self.burette.set_params(sigma=0.072, d_nozzle=2e-3, flow_rate=5e-8)
        self.lbl_feedback.setText("Тазаланды.")
        self._update_ui()

    def _update_ui(self):
        if self.burette.last_detach_mass is not None:
            m = self.burette.last_detach_mass
            self.mass_meter.set_value(m*1e6, vmax=max(1.0, m*1e6*2))
            flow = self.burette.flow_rate
            t_est = m / flow if flow > 1e-12 else 0.0
            self.time_meter.set_value(t_est, vmax=max(0.1, t_est*1.5))
        else:
            self.mass_meter.set_value(0.0, vmax=1.0)
            self.time_meter.set_value(0.0, vmax=1.0)
        self.lbl_model.setText(f"Модель: σ={self.burette.sigma_true:.5f} Н/м, d={self.burette.d_nozzle*1e3:.3f} мм")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabSurfaceTensionApp()
    win.show()
    sys.exit(app.exec())