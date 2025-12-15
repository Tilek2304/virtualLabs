# lab_diffraction_lambda.py
# Требуется: pip install PySide6
import sys, math, random, time
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer

def calc_lambda(a_m, d_m, b_m):
    # λ = a * b / d  (кичине бурчтар үчүн b/d ≈ sin φ)
    # формула так: a * sin(φ) = k * λ,  tan(φ) = b/d
    # λ = (a * b) / sqrt(b^2 + d^2)  (k=1 үчүн)
    # Бирок мектепте көбүнчө λ = a * b / d деп алышат (эгер b << d болсо)
    if d_m == 0: return None
    # Такыраак эсептөө (k=1):
    return (a_m * b_m) / math.sqrt(b_m**2 + d_m**2)

class MeterWidget(QFrame):
    def __init__(self, kind="λ (nm)", parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 100)
        self.kind = kind
        self.value = 0.0
        self.max_display = 1.0

    def set_value(self, val, vmax=None):
        self.value = val if val is not None else 0.0
        if vmax is not None:
            self.max_display = max(1e-12, float(vmax))
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
        p.setPen(QPen(Qt.black,2)); p.setFont(QFont("Sans",11,QFont.Bold))
        p.drawText(cx-18, cy+6, self.kind)
        p.setFont(QFont("Sans",9))
        if abs(self.value) < 1e-12:
            p.drawText(8, h-10, "—")
        else:
            if self.kind.startswith("λ"):
                p.drawText(8, h-10, f"{self.value*1e9:.1f} нм")
            else:
                p.drawText(8, h-10, f"{self.value:.4g}")

class DiffractionWidget(QFrame):
    """
    Дифракциялык торчо жана экран.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(820, 420)
        # Параметрлер
        self.a = 1e-6        # торчо мезгили (м)
        self.d = 1.0         # экранга чейинки аралык (м)
        self.lambda_true = 600e-9  # толкун узундугу (м)
        self.screen_x = None
        self.pattern_phase = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(40)
        self.k_max = 5

    def set_params(self, a=None, d=None, lambda_true=None):
        if a is not None: self.a = float(a)
        if d is not None: self.d = float(d)
        if lambda_true is not None: self.lambda_true = float(lambda_true)
        self.update()

    def _animate(self):
        self.pattern_phase += 0.06
        if self.pattern_phase > 2*math.pi:
            self.pattern_phase -= 2*math.pi
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(20,20,30))
        cx = 120
        self.screen_x = w - 120
        screen_w = 20
        
        # Торчо
        p.setPen(QPen(QColor(200,200,200), 1))
        for i in range(8):
            p.drawLine(cx + i*2, 40, cx + i*2, h-40)
        p.setFont(QFont("Sans",9)); p.setPen(QPen(Qt.white,1))
        # КОТОРМО: Grating -> Торчо
        p.drawText(cx-20, 24, "Торчо")

        # Экран
        p.setPen(QPen(QColor(180,180,200), 1)); p.setBrush(QColor(240,240,250, 40))
        p.drawRect(self.screen_x, 20, screen_w, h-40)

        # Максимумдар
        lam = self.lambda_true
        a = self.a
        d = self.d
        dx_m = float(self.screen_x - cx)
        px_per_m = dx_m / max(1e-6, d)
        center_y = h // 2
        max_positions = []
        for m in range(-self.k_max, self.k_max+1):
            # y_m ≈ m * λ * d / a (кичине бурчтар)
            # тагыраак: sin φ = m λ / a => y = d * tan φ
            sin_phi = m * lam / a if a!=0 else 0
            if abs(sin_phi) < 1.0:
                y_m_real = d * (sin_phi / math.sqrt(1 - sin_phi**2))
                y_m_px = center_y + int(y_m_real * px_per_m)
                if 20 <= y_m_px <= h-20:
                    max_positions.append((m, y_m_px))

        # Максимумдарды тартуу
        for (m, y_px) in max_positions:
            brightness = max(0.05, 1.0 - 0.12 * abs(m))
            # Түс толкун узундугуна жараша (болжол менен)
            # Жөнөкөйлүк үчүн сары-жашыл колдонобуз, же λ жараша өзгөртсө болот
            if 380e-9 <= lam <= 780e-9:
                # жөнөкөй RGB (спектр)
                hue = int(270 - (lam*1e9 - 380) * (270/400)) # 380->270(Violet), 780->0(Red) - болжол
                hue = max(0, min(359, hue))
                col = QColor.fromHsv(hue, 255, int(255*brightness))
            else:
                col = QColor(255, 255, 255, int(200 * brightness))
                
            p.setPen(Qt.NoPen); p.setBrush(col)
            p.drawRect(self.screen_x, y_px - 8, screen_w, 16)

        # Нурлар
        p.setPen(QPen(QColor(200,120,40,200), 1))
        for (m, y_px) in max_positions:
            p.setPen(QPen(QColor(200,120,40,120), 1, Qt.DashLine))
            p.drawLine(cx + 8, center_y, self.screen_x, y_px)

        # Текст
        p.setPen(QPen(Qt.white,1)); p.setFont(QFont("Sans",10))
        p.drawText(12, 18, f"a (мезгил) = {self.a*1e6:.3f} мкм")
        p.drawText(12, 36, f"d (аралык) = {self.d:.3f} м")
        p.drawText(12, 54, f"λ (модель) = {self.lambda_true*1e9:.1f} нм")
        
        # b (1-тартиптеги максимумга чейинки аралык)
        if len(max_positions) > 1:
             # 0 жана 1-тартиптер бар экенин текшерүү
             y0 = next((y for m, y in max_positions if m==0), None)
             y1 = next((y for m, y in max_positions if m==1), None)
             if y0 is not None and y1 is not None:
                 b_px = abs(y1 - y0)
                 b_real = b_px / px_per_m
                 # КОТОРМО: b (аралык...)
                 p.drawText(12, 72, f"b (максимумдар аралыгы) = {b_real*1e3:.3f} мм")

class LabDiffractionApp(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Дифракция и длина волны -> Дифракция жана толкун узундугун аныктоо (λ = a·b / √(b²+d²))
        self.setWindowTitle("Лабораториялык иш — Дифракция жана толкун узундугун аныктоо")
        self.setMinimumSize(1200, 720)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.diff = DiffractionWidget()
        left.addWidget(self.diff)

        meters = QHBoxLayout()
        self.meter = MeterWidget("λ (нм)")
        meters.addWidget(self.meter)
        left.addLayout(meters)

        # Правая панель
        # КОТОРМО: Заголовок
        right.addWidget(QLabel("<b>Тажрыйбанын параметрлери</b>"))
        self.input_a = QLineEdit(); self.input_a.setPlaceholderText("мисалы 2.00 (мкм)")
        self.input_d = QLineEdit(); self.input_d.setPlaceholderText("мисалы 1.00 (м)")
        self.input_lambda = QLineEdit(); self.input_lambda.setPlaceholderText("мисалы 600 (нм)")
        
        right.addWidget(QLabel("Торчо мезгили a (мкм)"))
        right.addWidget(self.input_a)
        right.addWidget(QLabel("Экранга чейинки аралык d (м)"))
        right.addWidget(self.input_d)
        right.addWidget(QLabel("Толкун узундугу λ (нм) — модель"))
        right.addWidget(self.input_lambda)

        right.addSpacing(6)
        # КОТОРМО: Режим -> Режим
        right.addWidget(QLabel("<b>Режим</b>"))
        self.chk_manual = QCheckBox("Кол менен жазуу (авто толтуруу жок)")
        right.addWidget(self.chk_manual)

        right.addSpacing(6)
        # КОТОРМО: Поля ученика -> Окуучунун эсептөөлөрү
        right.addWidget(QLabel("<b>Окуучунун эсептөөлөрү</b>"))
        self.input_b_mm = QLineEdit(); self.input_b_mm.setPlaceholderText("b (мм) — максимумдар аралыгы")
        self.input_lambda_user = QLineEdit(); self.input_lambda_user.setPlaceholderText("λ (нм) — сиздин эсептөө")
        right.addWidget(self.input_b_mm)
        right.addWidget(self.input_lambda_user)

        # Кнопки
        # КОТОРМО: Применить -> Колдонуу
        btn_apply = QPushButton("Колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        # КОТОРМО: Симулировать -> Симуляциялоо
        btn_simulate = QPushButton("Симуляциялоо")
        btn_simulate.clicked.connect(self.simulate_pattern)
        # КОТОРМО: Измерить -> Өлчөө
        btn_measure = QPushButton("Өлчөө")
        btn_measure.clicked.connect(self.measure)
        # КОТОРМО: Проверить λ -> λ текшерүү
        btn_check = QPushButton("λ текшерүү")
        btn_check.clicked.connect(self.check)
        # КОТОРМО: Показать ответ -> Жоопту көрсөтүү
        btn_show = QPushButton("Жоопту көрсөтүү")
        btn_show.clicked.connect(self.show_answer)
        # КОТОРМО: Случайный эксперимент -> Кокустан тандалган тажрыйба
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
        self.ui_timer.timeout.connect(self._update_meter)
        self.ui_timer.start(200)

    def apply_params(self):
        try:
            a_um = float(self.input_a.text()) if self.input_a.text().strip() else self.diff.a*1e6
            d_m = float(self.input_d.text()) if self.input_d.text().strip() else self.diff.d
            lam_nm = float(self.input_lambda.text()) if self.input_lambda.text().strip() else self.diff.lambda_true*1e9
        except Exception:
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "a, d жана λ үчүн сан маанилерин киргизиңиз.")
            return
        a_m = a_um * 1e-6
        lam_m = lam_nm * 1e-9
        self.diff.set_params(a=a_m, d=d_m, lambda_true=lam_m)
        # КОТОРМО: Параметры применены -> Параметрлер колдонулду
        self.lbl_feedback.setText("Параметрлер колдонулду.")
        self._update_meter()

    def simulate_pattern(self):
        self.diff.update()
        # КОТОРМО: Симуляция... -> Интерференциялык сүрөт жаңыланды.
        self.lbl_feedback.setText("Интерференциялык сүрөт жаңыланды.")
        self._update_meter()

    def measure(self):
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Кол режими: талаалар автоматтык толтурулбайт.")
            return
        a = self.diff.a
        d = self.diff.d
        lam = self.diff.lambda_true
        if a == 0:
            QMessageBox.information(self, "Маалымат", "a жок.")
            return
        
        # 1-тартиптеги максимумга чейинки аралыкты эсептөө
        sin_phi = lam / a
        if sin_phi >= 1:
            self.lbl_feedback.setText("Максимумдар көрүнбөйт (λ > a).")
            return
        
        b_real = d * (sin_phi / math.sqrt(1 - sin_phi**2))
        
        b_meas = b_real * (1 + random.uniform(-0.02, 0.02))
        b_mm = b_meas * 1e3
        self.input_b_mm.setText(f"{b_mm:.3f}")
        
        # λ эсептөө
        lam_calc = calc_lambda(a, d, b_real)
        if lam_calc is not None:
            self.input_lambda_user.setText(f"{lam_calc*1e9:.1f}")
        self.lbl_feedback.setText("Көрсөткүчтөр жазылды (кичине ката менен).")
        self._update_meter()

    def check(self):
        try:
            b_mm = float(self.input_b_mm.text())
            lam_user_nm = float(self.input_lambda_user.text())
            a_um = float(self.input_a.text()) if self.input_a.text().strip() else self.diff.a*1e6
            d_m = float(self.input_d.text()) if self.input_d.text().strip() else self.diff.d
        except Exception:
            QMessageBox.warning(self, "Ката", "b, λ, a жана d маанилерин киргизиңиз.")
            return
        b_m = b_mm * 1e-3
        a_m = a_um * 1e-6
        lam_user = lam_user_nm * 1e-9
        
        lam_calc = calc_lambda(a_m, d_m, b_m)
        lam_true = self.diff.lambda_true
        
        tol_calc = max(0.03 * abs(lam_calc) if lam_calc else 1e-9, 1e-9)
        tol_true = max(0.05 * abs(lam_true) if lam_true else 1e-9, 1e-9)
        
        ok_user = abs(lam_user - lam_calc) <= tol_calc
        ok_model = abs(lam_calc - lam_true) <= tol_true
        
        lines = []
        if ok_user:
            lines.append("✅ Сиздин λ эсебиңиз туура.")
        else:
            lines.append(f"❌ Сиздин λ эсебиңиз ката. λ_эсеп = {lam_calc*1e9:.1f} нм.")
        if ok_model:
            lines.append("✅ Чыныгы мааниге жакын.")
        else:
            lines.append(f"❌ Чыныгы мааниден айырмаланат: λ = {lam_true*1e9:.1f} нм.")
        self.lbl_feedback.setText("\n".join(lines))
        self._update_meter()

    def show_answer(self):
        a = self.diff.a
        d = self.diff.d
        lam = self.diff.lambda_true
        if a == 0:
            QMessageBox.information(self, "Маалымат", "a жок.")
            return
        
        sin_phi = lam / a
        if sin_phi >= 1:
            self.lbl_feedback.setText("Максимумдар жок.")
            return
            
        b_real = d * (sin_phi / math.sqrt(1 - sin_phi**2))
        
        self.input_b_mm.setText(f"{b_real*1e3:.3f}")
        self.input_lambda_user.setText(f"{lam*1e9:.1f}")
        self.lbl_feedback.setText("Туура маанилер көрсөтүлдү.")
        self._update_meter()

    def random_experiment(self):
        a_um = random.uniform(1.5, 4.0)
        d_m = random.uniform(0.5, 1.5)
        lam_nm = random.uniform(400.0, 700.0)
        self.input_a.setText(f"{a_um:.3f}")
        self.input_d.setText(f"{d_m:.3f}")
        self.input_lambda.setText(f"{lam_nm:.1f}")
        self.diff.set_params(a=a_um*1e-6, d=d_m, lambda_true=lam_nm*1e-9)
        self.input_b_mm.clear(); self.input_lambda_user.clear()
        self.lbl_feedback.setText("Жаңы тажрыйба даярдалды.")
        self._update_meter()

    def reset_all(self):
        self.input_a.clear(); self.input_d.clear(); self.input_lambda.clear()
        self.input_b_mm.clear(); self.input_lambda_user.clear()
        self.diff.set_params(a=1e-6, d=1.0, lambda_true=600e-9)
        self.lbl_feedback.setText("Тазаланды.")
        self._update_meter()

    def _update_meter(self):
        lam = self.diff.lambda_true
        self.meter.set_value(lam, vmax=max(1e-9, lam*2))
        self.lbl_model.setText(f"Модель: a={self.diff.a*1e6:.3f} мкм, d={self.diff.d:.3f} м, λ={self.diff.lambda_true*1e9:.1f} нм")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabDiffractionApp()
    win.show()
    sys.exit(app.exec())