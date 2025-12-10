# lab_refractive_index.py
# Зарыйтуу: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox, QComboBox
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
from PySide6.QtCore import Qt, QTimer, QPointF

def safe_sin_deg(deg):
    return math.sin(math.radians(deg))

def safe_asin(x):
    if x >= 1.0: return math.pi/2
    if x <= -1.0: return -math.pi/2
    return math.asin(x)

class PrismWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(760, 420)
        self.n_air = 1.0
        self.n_glass = 1.5
        self.a_deg = 30.0
        self.impact_x = 360
        self.t = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(30)

    def set_params(self, n_glass=None, a_deg=None, impact_x=None):
        if n_glass is not None: self.n_glass = float(n_glass)
        if a_deg is not None: self.a_deg = float(a_deg)
        if impact_x is not None: self.impact_x = int(impact_x)
        self.update()

    def _animate(self):
        self.t += 0.02
        if self.t > 2*math.pi: self.t -= 2*math.pi
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))
        cx = w//2; baseline = h//2
        src_x = 80; screen_x = w - 120
        glass_w = 220; glass_h = 220
        glass_x = cx - glass_w//2; glass_y = baseline - glass_h//2
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(200,230,255,200))
        p.drawRoundedRect(glass_x, glass_y, glass_w, glass_h, 8, 8)
        impact_x = glass_x + int((self.impact_x - 40) % glass_w); impact_y = baseline
        p.setPen(QPen(QColor(120,120,120),1, Qt.DashLine))
        p.drawLine(impact_x, glass_y, impact_x, glass_y + glass_h)
        a_rad = math.radians(self.a_deg)
        dx = impact_x - src_x
        y_src = impact_y - math.tan(a_rad) * dx
        p.setPen(QPen(QColor(220,100,40), 2))
        p.drawLine(src_x, int(y_src), impact_x, impact_y)
        sin_a = math.sin(a_rad)
        ratio = (self.n_air * sin_a) / (self.n_glass if self.n_glass!=0 else 1e-9)
        total_internal = False
        if abs(ratio) > 1.0:
            total_internal = True
            b_rad = None
        else:
            b_rad = safe_asin(ratio)
        if not total_internal and b_rad is not None:
            dx_inside = (glass_x + glass_w) - impact_x
            y_inside_end = impact_y + math.tan(b_rad) * dx_inside
            p.setPen(QPen(QColor(40,80,200), 2))
            p.drawLine(impact_x, impact_y, glass_x + glass_w, int(y_inside_end))
            sin_c = (self.n_glass * math.sin(b_rad)) / self.n_air
            if abs(sin_c) > 1.0:
                c_rad = None
            else:
                c_rad = safe_asin(sin_c)
                x_exit = glass_x + glass_w; y_exit = int(y_inside_end)
                x_screen = screen_x
                dx2 = x_screen - x_exit
                y_screen = y_exit + math.tan(c_rad) * dx2
                p.setPen(QPen(QColor(40,160,40), 2))
                p.drawLine(x_exit, y_exit, x_screen, int(y_screen))
                p.setPen(QPen(QColor(40,160,40), 1))
                p.drawEllipse(x_screen - 4, int(y_screen) - 4, 8, 8)
                p.drawText(x_screen + 8, int(y_screen) + 4, "Image")
        else:
            p.setPen(QPen(QColor(180,30,30), 2, Qt.DashLine))
            p.drawLine(impact_x, impact_y, glass_x, int(impact_y - math.tan(a_rad) * (impact_x - glass_x)))
            p.drawText(impact_x + 6, impact_y - 6, "TIR")
        p.setPen(QPen(Qt.black,1)); p.setBrush(QColor(255,220,80))
        p.drawEllipse(src_x - 12, int(y_src) - 12, 24, 24)
        p.drawText(src_x - 18, int(y_src) - 18, "Lamp")
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",10))
        p.drawText(12, 18, f"n (модель) = {self.n_glass:.3f}")
        p.drawText(12, 36, f"a = {self.a_deg:.2f}°")
        if not total_internal and b_rad is not None:
            p.drawText(12, 54, f"b (модель) = {math.degrees(b_rad):.2f}°")
        else:
            p.drawText(12, 54, "b (модель) = — (толук ички чагылуу)")

class LabRefractiveIndexApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сынык бөлүнүш көрсөткүчү - n = sin a / sin b")
        self.setMinimumSize(1100, 700)
        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)
        self.prism = PrismWidget()
        left.addWidget(self.prism)
        right.addWidget(QLabel("<b>Параметрлер</b>"))
        right.addWidget(QLabel("Айнектин сынык бөлүнүш көрсөткүчү n"))
        self.input_n = QLineEdit(); self.input_n.setPlaceholderText("мисалы 1.50")
        right.addWidget(self.input_n)
        right.addWidget(QLabel("Түшкү бурчу a (°)"))
        self.input_a = QLineEdit(); self.input_a.setPlaceholderText("мисалы 30")
        right.addWidget(self.input_a)
        right.addSpacing(6)
        right.addWidget(QLabel("<b>Башкаруу</b>"))
        self.slider_a = QSlider(Qt.Horizontal)
        self.slider_a.setRange(0, 89)
        self.slider_a.setValue(int(self.prism.a_deg))
        self.slider_a.valueChanged.connect(self.on_slider_a)
        right.addWidget(self.slider_a)
        self.lbl_a = QLabel(f"a = {self.prism.a_deg:.1f}°")
        right.addWidget(self.lbl_a)
        right.addSpacing(6)
        right.addWidget(QLabel("<b>Режим</b>"))
        self.chk_manual = QCheckBox("Кол режими")
        right.addWidget(self.chk_manual)
        right.addSpacing(6)
        right.addWidget(QLabel("<b>Студенттин талаалары</b>"))
        self.input_a_meas = QLineEdit(); self.input_a_meas.setPlaceholderText("a (°)")
        self.input_b_meas = QLineEdit(); self.input_b_meas.setPlaceholderText("b (°)")
        self.input_n_user = QLineEdit(); self.input_n_user.setPlaceholderText("n")
        right.addWidget(self.input_a_meas)
        right.addWidget(self.input_b_meas)
        right.addWidget(self.input_n_user)
        btn_apply = QPushButton("Параметрлерди колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        btn_measure = QPushButton("Өлчөө")
        btn_measure.clicked.connect(self.measure)
        btn_check = QPushButton("n текшер")
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
        right.addWidget(QLabel("<b>Жыйынтыктар</b>"))
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setWordWrap(True)
        right.addWidget(self.lbl_feedback)
        right.addStretch(1)
        self.random_experiment()
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(150)

    def on_slider_a(self, val):
        self.input_a.setText(str(val))
        self.prism.set_params(a_deg=val)
        self.lbl_a.setText(f"a = {val:.1f}°")
        self._update_ui()

    def apply_params(self):
        try:
            n = float(self.input_n.text()) if self.input_n.text().strip() else self.prism.n_glass
            a = float(self.input_a.text()) if self.input_a.text().strip() else self.prism.a_deg
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Киргизиңиз сандык маанилерди.")
            return
        self.prism.set_params(n_glass=n, a_deg=a)
        self.slider_a.setValue(int(a))
        self.lbl_feedback.setText("Параметрлер колдонулду.")
        self._update_ui()

    def measure(self):
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Кол режими.")
            return
        a = self.prism.a_deg
        n = self.prism.n_glass
        sin_a = safe_sin_deg(a)
        ratio = (self.prism.n_air * sin_a) / (n if n!=0 else 1e-9)
        if abs(ratio) > 1.0:
            self.input_a_meas.setText(f"{a:.2f}")
            self.input_b_meas.setText("")
            self.input_n_user.setText("")
            return
        b_rad = safe_asin(ratio)
        b_deg = math.degrees(b_rad)
        a_meas = a * (1 + random.uniform(-0.01, 0.01))
        b_meas = b_deg * (1 + random.uniform(-0.01, 0.01))
        n_calc = math.sin(math.radians(a_meas)) / math.sin(math.radians(b_meas)) if abs(math.sin(math.radians(b_meas)))>1e-9 else None
        self.input_a_meas.setText(f"{a_meas:.2f}")
        self.input_b_meas.setText(f"{b_meas:.2f}")
        self.input_n_user.setText(f"{n_calc:.4f}" if n_calc is not None else "")
        self.lbl_feedback.setText("Өлчөө аяктады.")
        self._update_ui()

    def check(self):
        try:
            a_user = float(self.input_a_meas.text())
            b_user = float(self.input_b_meas.text())
            n_user = float(self.input_n_user.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Киргизиңиз маанилерди.")
            return
        if abs(math.sin(math.radians(b_user))) < 1e-9:
            return
        n_calc = math.sin(math.radians(a_user)) / math.sin(math.radians(b_user))
        n_true = self.prism.n_glass
        tol_calc = max(0.03 * abs(n_calc), 1e-3)
        tol_true = max(0.05 * abs(n_true), 1e-3)
        ok_user = abs(n_user - n_calc) <= tol_calc
        ok_model = abs(n_calc - n_true) <= tol_true
        if ok_user and ok_model:
            self.lbl_feedback.setText("✅ Туура!")
        else:
            self.lbl_feedback.setText("❌ Жалган.")
        self._update_ui()

    def show_answer(self):
        a = self.prism.a_deg
        n = self.prism.n_glass
        sin_a = safe_sin_deg(a)
        ratio = (self.prism.n_air * sin_a) / (n if n!=0 else 1e-9)
        if abs(ratio) > 1.0:
            self.input_a_meas.setText(f"{a:.2f}")
            self.input_b_meas.setText("")
            self.input_n_user.setText("")
            return
        b_rad = safe_asin(ratio)
        b_deg = math.degrees(b_rad)
        n_calc = math.sin(math.radians(a)) / math.sin(math.radians(b_deg)) if abs(math.sin(math.radians(b_deg)))>1e-9 else None
        self.input_a_meas.setText(f"{a:.2f}")
        self.input_b_meas.setText(f"{b_deg:.2f}")
        self.input_n_user.setText(f"{n_calc:.4f}" if n_calc is not None else "")
        self.lbl_feedback.setText("Жооп көрсөтүлдү.")
        self._update_ui()

    def random_experiment(self):
        n = random.uniform(1.3, 1.8)
        a = random.uniform(20.0, 75.0)
        self.input_n.setText(f"{n:.3f}")
        self.input_a.setText(f"{a:.1f}")
        self.prism.set_params(n_glass=n, a_deg=a)
        self.slider_a.setValue(int(a))
        self.input_a_meas.clear(); self.input_b_meas.clear(); self.input_n_user.clear()
        self.lbl_feedback.setText("Кокус эксперимент түзүлдү.")
        self._update_ui()

    def reset_all(self):
        self.input_n.clear(); self.input_a.clear()
        self.input_a_meas.clear(); self.input_b_meas.clear(); self.input_n_user.clear()
        self.prism.set_params(n_glass=1.5, a_deg=30.0)
        self.slider_a.setValue(30)
        self.lbl_feedback.setText("Сброс.")
        self._update_ui()

    def _update_ui(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabRefractiveIndexApp()
    win.show()
    sys.exit(app.exec())
