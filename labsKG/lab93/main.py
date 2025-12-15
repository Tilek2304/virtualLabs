# lab_young_spring.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox, QDoubleSpinBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
from PySide6.QtCore import Qt, QTimer, QPointF

# Универсалдуу аналогдук прибор
class MeterWidget(QFrame):
    def __init__(self, kind="N", parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.kind = kind
        self.value = 0.0
        self.max_display = 10.0

    def set_value(self, val, vmax=None):
        self.value = val if val is not None else 0.0
        if vmax is not None:
            self.max_display = max(1e-6, float(vmax))
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
        p.drawText(cx-8, cy+6, self.kind)
        p.setFont(QFont("Sans",9))
        p.drawText(8, h-10, f"{self.value:.2f} {self.kind}")

# Пружина жана динамометр (анимация)
class SpringWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 420)
        # Моделдин параметрлери
        self.k_true = 50.0  # Н/м
        self.rest_length = 120.0  # тынч абалдагы узундук (px)
        self.mass_attached = 0.0  # кг
        self.g = 9.81
        self.force_external = 0.0  # тышкы күч (Н)
        # Визуалдык
        self.current_length = self.rest_length
        self.target_length = self.rest_length
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def set_params(self, k=None, rest_length=None):
        if k is not None: self.k_true = float(k)
        if rest_length is not None: self.rest_length = float(rest_length)
        self.current_length = self.rest_length
        self.target_length = self.rest_length
        self.update()

    def apply_mass(self, m):
        self.mass_attached = float(m)
        F = self.mass_attached * self.g
        self.force_external = F
        self._update_target_length()

    def apply_force(self, F):
        self.force_external = float(F)
        self._update_target_length()

    def _update_target_length(self):
        px_per_N = 100.0
        x_m = self.force_external / self.k_true if self.k_true != 0 else 0.0
        x_px = x_m * px_per_N
        self.target_length = self.rest_length + x_px
        self.target_length = max(self.rest_length, min(self.rest_length + 600, self.target_length))
        self.update()

    def _tick(self):
        d = self.target_length - self.current_length
        self.current_length += d * 0.18
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))

        cx = w // 2
        top = 40
        # Бекиткич
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(160,160,160))
        p.drawRect(cx - 40, top - 12, 80, 12)
        # Пружина
        y0 = top + 6
        y1 = int(top + self.current_length)
        segments = 18
        width = 40
        p.setPen(QPen(QColor(120,60,20), 3))
        pts = []
        for i in range(segments + 1):
            t = i / segments
            x = cx + (math.sin(t * math.pi * 6) * (width * (1 - t*0.6)))
            y = y0 + t * (y1 - y0)
            pts.append((x, y))
        for i in range(len(pts)-1):
            p.drawLine(int(pts[i][0]), int(pts[i][1]), int(pts[i+1][0]), int(pts[i+1][1]))
        
        # Жүк (блок)
        block_w, block_h = 120, 40
        bx = cx - block_w//2
        by = y1
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(200,200,220))
        p.drawRect(bx, by, block_w, block_h)
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",10))
        p.drawText(bx + 8, by + 24, f"m = {self.mass_attached:.3f} кг")

        # Текст
        px_per_N = 100.0
        x_px = self.current_length - self.rest_length
        x_m = x_px / px_per_N
        F_now = self.force_external
        # КОТОРМО: k (модель) -> k (чыныгы)
        p.drawText(12, 20, f"k (чыныгы) = {self.k_true:.2f} Н/м")
        p.drawText(12, 40, f"F = {F_now:.3f} Н")
        p.drawText(12, 60, f"x = {x_m:.4f} м (≈{x_px:.1f} px)")

class LabYoungApp(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Гук мыйзамы — k = F / x
        self.setWindowTitle("Лабораториялык иш — Гук мыйзамы (k = F / x)")
        self.setMinimumSize(1100, 700)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.spring = SpringWidget()
        left.addWidget(self.spring)

        meters = QHBoxLayout()
        self.dynamometer = MeterWidget("N")
        meters.addWidget(self.dynamometer)
        left.addLayout(meters)

        # Правая панель
        # КОТОРМО: Заголовок
        right.addWidget(QLabel("<b>Пружинанын параметрлери</b>"))
        self.input_k = QLineEdit(); self.input_k.setPlaceholderText("k (Н/м) — моделдин катуулугу")
        self.input_rest = QLineEdit(); self.input_rest.setPlaceholderText("Тынч абал узундугу (px)")
        right.addWidget(self.input_k)
        right.addWidget(self.input_rest)

        right.addSpacing(6)
        # КОТОРМО: Күч / Масса
        right.addWidget(QLabel("<b>Коюлган күч / масса</b>"))
        # КОТОРМО: Задавать силу вручную -> Күчтү кол менен берүү
        self.chk_force_mode = QCheckBox("Күчтү кол менен берүү (болбосо — масса кошуу)")
        right.addWidget(self.chk_force_mode)
        
        mass_row = QHBoxLayout()
        self.input_mass = QLineEdit(); self.input_mass.setPlaceholderText("m (кг) — жүктүн массасы")
        mass_row.addWidget(self.input_mass)
        # КОТОРМО: Добавить груз -> Жүктү кошуу
        btn_add_mass = QPushButton("Жүктү кошуу")
        btn_add_mass.clicked.connect(self.add_mass)
        mass_row.addWidget(btn_add_mass)
        right.addLayout(mass_row)
        
        # КОТОРМО: Күч F (Н) — жылдыргыч
        right.addWidget(QLabel("Күч F (Н) — жылдыргыч"))
        self.slider_F = QSlider(Qt.Horizontal)
        self.slider_F.setRange(0, 500)
        self.slider_F.setValue(0)
        self.slider_F.valueChanged.connect(self.on_slider_F)
        right.addWidget(self.slider_F)
        self.lbl_F = QLabel("F = 0.00 Н")
        right.addWidget(self.lbl_F)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Режим</b>"))
        # КОТОРМО: Ручной режим -> Кол менен жазуу (авто толтуруу жок)
        self.chk_manual = QCheckBox("Кол менен жазуу (авто толтуруу жок)")
        right.addWidget(self.chk_manual)

        right.addSpacing(6)
        # КОТОРМО: Окуучунун жооптору
        right.addWidget(QLabel("<b>Окуучунун жооптору</b>"))
        self.input_F_meas = QLineEdit(); self.input_F_meas.setPlaceholderText("F (Н) — өлчөнгөн күч")
        self.input_x_meas = QLineEdit(); self.input_x_meas.setPlaceholderText("x (м) — узаруу")
        self.input_k_user = QLineEdit(); self.input_k_user.setPlaceholderText("k (Н/м) — сиздин эсептөө")
        
        right.addWidget(self.input_F_meas)
        right.addWidget(self.input_x_meas)
        right.addWidget(self.input_k_user)

        # Кнопки
        # КОТОРМО: Применить -> Колдонуу
        btn_apply = QPushButton("Колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        # КОТОРМО: Измерить -> Өлчөө (көрсөткүчтөрдү алуу)
        btn_measure = QPushButton("Өлчөө (көрсөткүчтөрдү алуу)")
        btn_measure.clicked.connect(self.measure)
        # КОТОРМО: Проверить k -> k текшерүү
        btn_check = QPushButton("k текшерүү")
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
        right.addWidget(btn_measure)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        right.addSpacing(8)
        # КОТОРМО: Результаты -> Жыйынтыктар
        right.addWidget(QLabel("<b>Жыйынтыктар</b>"))
        self.lbl_Fnow = QLabel("F (модель): — Н")
        self.lbl_xnow = QLabel("x (модель): — м")
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setWordWrap(True)
        right.addWidget(self.lbl_Fnow)
        right.addWidget(self.lbl_xnow)
        right.addWidget(self.lbl_feedback)
        right.addStretch(1)

        self.random_experiment()
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_meter)
        self.ui_timer.start(150)

    def on_slider_F(self, val):
        F = val / 100.0
        self.lbl_F.setText(f"F = {F:.2f} Н")
        if self.chk_force_mode.isChecked():
            self.spring.apply_force(F)
            self._update_labels()

    def apply_params(self):
        try:
            k = float(self.input_k.text()) if self.input_k.text().strip() else self.spring.k_true
            rest = float(self.input_rest.text()) if self.input_rest.text().strip() else self.spring.rest_length
        except Exception:
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "k жана узундук үчүн сан маанилерин киргизиңиз.")
            return
        self.spring.set_params(k=k, rest_length=rest)
        self.input_F_meas.clear(); self.input_x_meas.clear(); self.input_k_user.clear()
        # КОТОРМО: Параметры применены -> Параметрлер колдонулду
        self.lbl_feedback.setText("Параметрлер колдонулду. Жүктү кошуңуз же күчтү жылдыргыч менен өзгөртүңүз.")
        self._update_labels()

    def add_mass(self):
        try:
            m = float(self.input_mass.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "Массаны сан түрүндө киргизиңиз (кг).")
            return
        if self.chk_force_mode.isChecked():
            QMessageBox.information(self, "Маалымат", "Адегенде «Күчтү кол менен берүү» режимин өчүрүңүз.")
            return
        self.spring.apply_mass(m)
        self.lbl_feedback.setText(f"Жүк m = {m:.3f} кг кошулду. «Өлчөө» баскычын басыңыз.")
        self._update_labels()

    def measure(self):
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Кол режими: талаалар автоматтык толтурулбайт.")
            self._update_labels()
            return
        
        px_per_N = 100.0
        x_px = self.spring.current_length - self.spring.rest_length
        x_m = x_px / px_per_N
        F = self.spring.force_external
        
        F_meas = F * (1 + random.uniform(-0.02, 0.02))
        x_meas = x_m * (1 + random.uniform(-0.015, 0.015))
        
        self.input_F_meas.setText(f"{F_meas:.3f}")
        self.input_x_meas.setText(f"{x_meas:.4f}")
        self.lbl_feedback.setText("Көрсөткүчтөр жазылды (кичине ката менен).")
        self._update_labels()

    def check(self):
        try:
            F_user = float(self.input_F_meas.text())
            x_user = float(self.input_x_meas.text())
            k_user = float(self.input_k_user.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "F, x, k маанилерин киргизиңиз.")
            return
        
        if abs(x_user) < 1e-6:
            QMessageBox.information(self, "Маалымат", "x өтө аз.")
            return
            
        k_calc = F_user / x_user
        k_true = self.spring.k_true
        tol = max(0.03 * abs(k_true), 1e-3)
        ok_user = abs(k_user - k_calc) <= max(0.02 * abs(k_calc), 1e-3)
        ok_true = abs(k_calc - k_true) <= tol
        
        lines = []
        if ok_user:
            lines.append("✅ Сиздин k эсебиңиз туура.")
        else:
            lines.append(f"❌ Сиздин k эсебиңиз ката. k_эсеп = {k_calc:.3f} Н/м.")
        if ok_true:
            lines.append("✅ Чыныгы мааниге жакын.")
        else:
            lines.append(f"❌ Чыныгы мааниден айырмаланат: k = {k_true:.3f} Н/м.")
        self.lbl_feedback.setText("\n".join(lines))

    def show_answer(self):
        px_per_N = 100.0
        x_px = self.spring.current_length - self.spring.rest_length
        x_m = x_px / px_per_N
        F = self.spring.force_external
        if abs(x_m) < 1e-9:
            QMessageBox.information(self, "Маалымат", "x жок.")
            return
        k_calc = F / x_m
        self.input_F_meas.setText(f"{F:.3f}")
        self.input_x_meas.setText(f"{x_m:.4f}")
        self.input_k_user.setText(f"{k_calc:.3f}")
        self.lbl_feedback.setText("Туура маанилер көрсөтүлдү.")
        self._update_labels()

    def random_experiment(self):
        k = random.uniform(10.0, 200.0)
        rest = random.uniform(80.0, 160.0)
        m = random.uniform(0.02, 0.8)
        self.input_k.setText(f"{k:.2f}")
        self.input_rest.setText(f"{rest:.1f}")
        self.input_mass.setText(f"{m:.3f}")
        self.spring.set_params(k=k, rest_length=rest)
        self.spring.apply_mass(m)
        self.input_F_meas.clear(); self.input_x_meas.clear(); self.input_k_user.clear()
        self.lbl_feedback.setText("Жаңы тажрыйба даярдалды.")
        self._update_labels()

    def reset_all(self):
        self.input_k.clear(); self.input_rest.clear(); self.input_mass.clear()
        self.input_F_meas.clear(); self.input_x_meas.clear(); self.input_k_user.clear()
        self.chk_force_mode.setChecked(False); self.chk_manual.setChecked(False)
        self.spring.set_params(k=50.0, rest_length=120.0)
        self.spring.mass_attached = 0.0
        self.spring.force_external = 0.0
        self.spring.current_length = self.spring.rest_length
        self.spring.target_length = self.spring.rest_length
        self.lbl_feedback.setText("Тазаланды.")
        self._update_labels()

    def _update_meter(self):
        F_now = self.spring.force_external
        self.dynamometer.set_value(F_now, vmax=max(0.1, max(1.0, F_now*1.5)))
        px_per_N = 100.0
        x_px = self.spring.current_length - self.spring.rest_length
        x_m = x_px / px_per_N
        self.lbl_Fnow.setText(f"F (модель): {F_now:.3f} Н")
        self.lbl_xnow.setText(f"x (модель): {x_m:.4f} м")

    def _update_labels(self):
        self._update_meter()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabYoungApp()
    win.show()
    sys.exit(app.exec())