# lab_electromagnet.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox, QSpinBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer

class ElectromagnetWidget(QFrame):
    """
    Катушка жана компас.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 360)
        # Параметрлер
        self.I = 0.0         # ток, А
        self.N = 50          # ороолордун саны
        self.mu = 1.0        # өзөктүн магниттик өткөрүмдүүлүгү
        self.k = 0.08        # коэффициент B -> бурулуу бурчу
        self.theta_max = 85  # максималдуу бурч
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        self.current_theta = 0.0
        self.target_theta = 0.0

    def set_params(self, I=None, N=None, mu=None):
        if I is not None:
            self.I = float(I)
        if N is not None:
            self.N = int(N)
        if mu is not None:
            self.mu = float(mu)
        self._recompute()
        self.update()

    def _recompute(self):
        # Жөнөкөй модель: B ~ mu * N * I
        B = self.mu * self.N * self.I
        # Бурулуу бурчу (тангенс функциясы менен чектелет)
        self.target_theta = self.theta_max * math.tanh(self.k * B)

    def animate(self):
        d = self.target_theta - self.current_theta
        if abs(d) > 0.01:
            self.current_theta += d * 0.12
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250, 250, 250))

        # Катушканын координаталары
        cx = w // 3
        cy = h // 2
        coil_w = 220
        coil_h = 120

        # Корпус
        p.setPen(QPen(Qt.black, 2))
        p.setBrush(QColor(230, 230, 240))
        p.drawRoundedRect(cx - coil_w // 2, cy - coil_h // 2, coil_w, coil_h, 10, 10)

        # Ороолор (витки)
        p.setPen(QPen(QColor(120, 60, 20), 2))
        turns = min(40, max(6, self.N // 2))
        for i in range(turns):
            t = i / max(1, turns - 1)
            left = cx - coil_w // 2 + 12
            right = cx + coil_w // 2 - 12
            y = cy - coil_h // 2 + 12 + t * (coil_h - 24)
            p.drawArc(left, int(y) - 8, right - left, 16, 0, 180 * 16)

        # Өзөк (Сердечник)
        if self.mu > 1.05:
            p.setBrush(QColor(200, 200, 210))
            p.setPen(QPen(QColor(80, 80, 120), 1))
            core_w = coil_w // 4
            core_h = coil_h - 24
            p.drawRoundedRect(cx - core_w // 2, cy - core_h // 2, core_w, core_h, 6, 6)
            p.setFont(QFont("Sans", 9))
            p.setPen(QPen(Qt.black, 1))
            # КОТОРМО: Железный сердечник -> Темир өзөк
            p.drawText(cx - core_w // 2, cy - core_h // 2 - 8, "Темир өзөк")

        # Параметрлерди жазуу
        p.setFont(QFont("Sans", 10))
        p.setPen(QPen(Qt.black, 1))
        p.drawText(cx - coil_w // 2, cy + coil_h // 2 + 20, f"I = {self.I:.2f} A")
        p.drawText(cx - coil_w // 2 + 120, cy + coil_h // 2 + 20, f"N = {self.N}")

        # Компас
        comp_x = 2 * w // 3
        comp_y = cy
        radius = 60
        p.setPen(QPen(Qt.black, 2))
        p.setBrush(QColor(255, 255, 255))
        p.drawEllipse(comp_x - radius, comp_y - radius, 2 * radius, 2 * radius)
        
        # N S
        p.setFont(QFont("Sans", 10, QFont.Bold))
        p.drawText(comp_x - 6, comp_y - radius + 18, "N")
        p.drawText(comp_x - 6, comp_y + radius - 6, "S")
        
        # Жебе (Стрелка)
        theta_rad = math.radians(self.current_theta)
        B = self.mu * self.N * self.I
        strength = abs(math.tanh(self.k * B))
        length = 0.6 * radius * (0.4 + 0.6 * strength)
        
        # Оң жагы (кызыл)
        p.setPen(QPen(QColor(200, 30, 30), 3))
        x_end = comp_x + length * math.sin(theta_rad)
        y_end = comp_y - length * math.cos(theta_rad)
        p.drawLine(comp_x, comp_y, int(x_end), int(y_end))
        
        # Сол жагы (көк)
        p.setPen(QPen(QColor(30, 30, 200), 2))
        x_tail = comp_x - 0.4 * length * math.sin(theta_rad)
        y_tail = comp_y + 0.4 * length * math.cos(theta_rad)
        p.drawLine(comp_x, comp_y, int(x_tail), int(y_tail))
        
        # Бурчтун мааниси
        p.setPen(QPen(Qt.black, 1))
        p.setFont(QFont("Sans", 9))
        p.drawText(comp_x - 40, comp_y + radius + 18, f"θ ≈ {self.current_theta:.1f}°")

class LabElectromagnetApp(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Электромагнит -> Электромагнитти чогултуу жана анын касиетин сыноо
        self.setWindowTitle("Лабораториялык иш — Электромагнитти чогултуу")
        self.setMinimumSize(1000, 560)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.widget = ElectromagnetWidget()
        left.addWidget(self.widget)

        # Правая панель
        # КОТОРМО: Заголовок
        right.addWidget(QLabel("<b>Электромагнит: катушка жана компас</b>"))
        
        # КОТОРМО: Инструкция
        info = QLabel("Ток күчүн, ороолордун санын өзгөртүп жана темир өзөктү салып көрүңүз.\nКомпастын жебесинин кыйшаюусун байкаңыз.")
        info.setWordWrap(True)
        right.addWidget(info)

        # Ток
        right.addWidget(QLabel("<b>Ток күчү I (A)</b>"))
        self.slider_I = QSlider(Qt.Horizontal)
        self.slider_I.setMinimum(0); self.slider_I.setMaximum(500)
        self.slider_I.setValue(0)
        self.slider_I.valueChanged.connect(self.on_slider)
        right.addWidget(self.slider_I)
        self.lbl_I = QLabel("I = 0.00 A")
        right.addWidget(self.lbl_I)

        # Ороолордун саны
        right.addWidget(QLabel("<b>Ороолордун саны N</b>"))
        self.spin_N = QSpinBox(); self.spin_N.setRange(10, 1000); self.spin_N.setValue(50)
        right.addWidget(self.spin_N)

        # Өзөк
        # КОТОРМО: Железный сердечник -> Темир өзөк (күчөтүү)
        self.chk_core = QCheckBox("Темир өзөк (күчөтүү)")
        right.addWidget(self.chk_core)

        right.addSpacing(6)
        # КОТОРМО: Наблюдения -> Байкоолор (окуучу жазат)
        right.addWidget(QLabel("<b>Байкоолор (окуучу жазат)</b>"))
        self.input_I_user = QLineEdit(); self.input_I_user.setPlaceholderText("I (A) — сиздин байкооңуз")
        self.input_theta_user = QLineEdit(); self.input_theta_user.setPlaceholderText("θ (°) — компастын кыйшаюусу")
        right.addWidget(self.input_I_user)
        right.addWidget(self.input_theta_user)

        # Кнопки
        # КОТОРМО: Применить -> Колдонуу
        btn_apply = QPushButton("Колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        # КОТОРМО: Случайный эксперимент -> Кокустан тандалган тажрыйба
        btn_random = QPushButton("Кокустан тандалган тажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        # КОТОРМО: Проверить -> Текшерүү
        btn_check = QPushButton("Текшерүү")
        btn_check.clicked.connect(self.check)
        # КОТОРМО: Показать ответ -> Жоопту көрсөтүү
        btn_show = QPushButton("Жоопту көрсөтүү")
        btn_show.clicked.connect(self.show_answer)
        # КОТОРМО: Сброс -> Кайра баштоо
        btn_reset = QPushButton("Кайра баштоо")
        btn_reset.clicked.connect(self.reset)

        right.addWidget(btn_apply)
        right.addWidget(btn_random)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_reset)

        self.lbl_result = QLabel("")
        right.addWidget(self.lbl_result)
        right.addStretch(1)

        self.random_experiment()

    def on_slider(self, val):
        I = val / 100.0
        self.lbl_I.setText(f"I = {I:.2f} A")
        self.widget.set_params(I=None, N=None, mu=None)
        self.widget.I = I
        self.widget._recompute()
        self.widget.update()

    def apply_params(self):
        try:
            I = self.slider_I.value() / 100.0
            N = self.spin_N.value()
            mu = 4.0 if self.chk_core.isChecked() else 1.0
        except Exception:
            QMessageBox.warning(self, "Ката", "Туура эмес параметрлер.")
            return
        self.widget.set_params(I=I, N=N, mu=mu)
        # КОТОРМО: Параметры применены -> Параметрлер колдонулду
        self.lbl_result.setText("Параметрлер колдонулду. Компастын кыйшаюусун байкаңыз.")

    def random_experiment(self):
        I = random.uniform(0.0, 3.0)
        N = random.choice([30, 50, 100, 200])
        core = random.choice([False, True])
        self.slider_I.setValue(int(I * 100))
        self.spin_N.setValue(N)
        self.chk_core.setChecked(core)
        self.apply_params()
        self.input_I_user.clear(); self.input_theta_user.clear()
        self.lbl_result.setText("Жаңы тажрыйба даярдалды.")

    def check(self):
        try:
            I_user = float(self.input_I_user.text())
            theta_user = float(self.input_theta_user.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "I жана θ үчүн сан маанилерин киргизиңиз.")
            return
        I_true = self.widget.I
        theta_true = self.widget.target_theta
        tol_I = max(0.05 * max(1.0, I_true), 0.02)
        tol_theta = max(0.08 * max(1.0, abs(theta_true)), 1.0)
        ok_I = abs(I_user - I_true) <= tol_I
        ok_theta = abs(theta_user - theta_true) <= tol_theta
        
        lines = []
        if ok_I:
            lines.append("✅ I туура өлчөндү.")
        else:
            lines.append(f"❌ I туура эмес (туурасы {I_true:.2f} A).")
        if ok_theta:
            lines.append("✅ θ туура өлчөндү.")
        else:
            lines.append(f"❌ θ туура эмес (туурасы ≈ {theta_true:.1f}°).")
        self.lbl_result.setText("\n".join(lines))

    def show_answer(self):
        I_true = self.widget.I
        theta_true = self.widget.target_theta
        self.input_I_user.setText(f"{I_true:.2f}")
        self.input_theta_user.setText(f"{theta_true:.1f}")
        self.lbl_result.setText("Туура маанилер көрсөтүлдү.")

    def reset(self):
        self.slider_I.setValue(0)
        self.spin_N.setValue(50)
        self.chk_core.setChecked(False)
        self.apply_params()
        self.input_I_user.clear(); self.input_theta_user.clear()
        self.lbl_result.setText("Кайра башталды.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabElectromagnetApp()
    win.show()
    sys.exit(app.exec())