# lab_motor.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer

class MeterWidget(QFrame):
    def __init__(self, title="Meter", min_val=0, max_val=10, unit="", parent=None):
        super().__init__(parent)
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self.unit = unit
        self.value = 0.0
        self.setMinimumSize(150, 120)

    def set_value(self, val):
        self.value = max(self.min_val, min(self.max_val, val))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(255,255,255))
        p.setPen(QPen(Qt.black, 1))
        p.drawRect(0, 0, w-1, h-1)

        font_title = QFont("Sans", 10, QFont.Bold)
        p.setFont(font_title)
        p.drawText(10, 5, w-20, 20, Qt.AlignHCenter, self.title)

        p.setPen(QPen(Qt.gray, 1))
        for i in range(6):
            y = 30 + i * 12
            p.drawLine(10, y, w-10, y)
            tick_val = self.min_val + (self.max_val - self.min_val) * i / 5
            p.setFont(QFont("Sans",8))
            p.drawText(5, y-4, 35, 12, Qt.AlignRight, f"{tick_val:.1f}")

        norm = (self.value - self.min_val) / max(1, (self.max_val - self.min_val))
        norm = max(0, min(1, norm))
        y_indicator = 30 + norm * 60
        p.setPen(QPen(QColor(220, 30, 30), 2))
        p.drawLine(45, int(y_indicator), w-10, int(y_indicator))
        p.fillRect(int(w-30), int(y_indicator)-4, 20, 8, QColor(220, 30, 30))

        p.setFont(QFont("Sans", 11, QFont.Bold))
        p.drawText(10, h-25, w-20, 20, Qt.AlignHCenter, f"{self.value:.2f} {self.unit}")

class MotorWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 400)
        self.U = 0.0
        self.I = 0.0
        self.omega = 0.0
        self.reversed = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)
        self.rotation = 0.0

    def set_params(self, U=None, I=None, reversed=None):
        if U is not None:
            self.U = float(U)
        if I is not None:
            self.I = float(I)
        if reversed is not None:
            self.reversed = bool(reversed)
        self._recompute()

    def _recompute(self):
        P = max(0, self.U * self.I - 0.5)
        self.omega = 20.0 * math.sqrt(max(0, P))
        if self.reversed:
            self.omega = -self.omega

    def update_animation(self):
        self.rotation += self.omega * 0.03
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))

        p.setFont(QFont("Sans",14,QFont.Bold))
        p.setPen(QPen(Qt.black,1))
        p.drawText(10, 10, w-20, 30, Qt.AlignLeft, "Электр двигателі")

        cx = w // 2
        cy = h // 2
        radius = 80

        p.setPen(QPen(QColor(100,100,100), 2))
        p.setBrush(QColor(200,200,200))
        p.drawEllipse(cx - radius, cy - radius, 2*radius, 2*radius)

        p.setBrush(QColor(150,150,200))
        p.setPen(QPen(QColor(80,80,150), 2))
        rotor_w = 50
        rotor_h = 30
        p.save()
        p.translate(cx, cy)
        p.rotate(self.rotation)
        p.drawRoundedRect(-rotor_w//2, -rotor_h//2, rotor_w, rotor_h, 5, 5)
        p.restore()

        p.setFont(QFont("Sans",9))
        p.setPen(QPen(Qt.black,1))

        info_y = cy + radius + 20
        p.drawText(cx - 100, info_y, 90, 20, Qt.AlignLeft, f"U = {self.U:.1f} V")
        p.drawText(cx + 10, info_y, 90, 20, Qt.AlignLeft, f"I = {self.I:.2f} A")
        p.drawText(cx - 100, info_y + 25, 90, 20, Qt.AlignLeft, f"P ≈ {self.U*self.I:.1f} W")

        speed_rpm = abs(self.omega) * 10
        p.drawText(cx + 10, info_y + 25, 90, 20, Qt.AlignLeft, f"n ≈ {speed_rpm:.0f} об/мин")

        if self.reversed:
            p.setFont(QFont("Sans",10,QFont.Bold))
            p.setPen(QPen(QColor(220,0,0),1))
            p.drawText(cx - 50, info_y + 50, 100, 20, Qt.AlignHCenter, "ТЕСКЕРИЛГЕН")

class LabMotorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык — Электр двигателі")
        self.setMinimumSize(1100, 700)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.motor = MotorWidget()
        left.addWidget(self.motor)

        right.addWidget(QLabel("<b>Электр двигателі сызаттуу</b>"))
        info = QLabel("Чыңалууну жана агымды өзгөртүңүз. Ротордун айланышын байкаңыз.")
        info.setWordWrap(True)
        right.addWidget(info)

        right.addWidget(QLabel("<b>Чыңалуу U (V)</b>"))
        self.slider_U = QSlider(Qt.Horizontal)
        self.slider_U.setMinimum(0); self.slider_U.setMaximum(240)
        self.slider_U.setValue(0)
        self.slider_U.valueChanged.connect(self.on_slider_U)
        right.addWidget(self.slider_U)
        self.lbl_U = QLabel("U = 0 V")
        right.addWidget(self.lbl_U)

        right.addWidget(QLabel("<b>Агым I (A)</b>"))
        self.slider_I = QSlider(Qt.Horizontal)
        self.slider_I.setMinimum(0); self.slider_I.setMaximum(300)
        self.slider_I.setValue(0)
        self.slider_I.valueChanged.connect(self.on_slider_I)
        right.addWidget(self.slider_I)
        self.lbl_I = QLabel("I = 0.00 A")
        right.addWidget(self.lbl_I)

        self.chk_reverse = QCheckBox("Ток багытын тескерилүүсү (сыман)")
        right.addWidget(self.chk_reverse)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Окуучунун экспериментүүсү</b>"))
        self.input_U = QLineEdit(); self.input_U.setPlaceholderText("U (V)")
        self.input_I = QLineEdit(); self.input_I.setPlaceholderText("I (A)")
        self.input_P = QLineEdit(); self.input_P.setPlaceholderText("P (W)")
        right.addWidget(self.input_U)
        right.addWidget(self.input_I)
        right.addWidget(self.input_P)

        btn_apply = QPushButton("Колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        btn_random = QPushButton("Кездейсоқ таажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        btn_check = QPushButton("Текшерүү")
        btn_check.clicked.connect(self.check)
        btn_show = QPushButton("Жоопту көрсөтүү")
        btn_show.clicked.connect(self.show_answer)
        btn_reset = QPushButton("Сброс")
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

    def on_slider_U(self, val):
        self.lbl_U.setText(f"U = {val} V")
        self.motor.U = float(val)

    def on_slider_I(self, val):
        self.lbl_I.setText(f"I = {val/100:.2f} A")
        self.motor.I = float(val) / 100.0

    def on_reverse_changed(self):
        self.motor.reversed = self.chk_reverse.isChecked()
        self.motor._recompute()

    def apply_params(self):
        self.motor.set_params(
            U=self.slider_U.value(),
            I=self.slider_I.value()/100.0,
            reversed=self.chk_reverse.isChecked()
        )
        self.lbl_result.setText("Параметрлер колдонулду. Ротордун айланышын байкаңыз.")

    def random_experiment(self):
        U = random.randint(0, 240)
        I = random.uniform(0.0, 3.0)
        reverse = random.choice([False, True])
        self.slider_U.setValue(U)
        self.slider_I.setValue(int(I*100))
        self.chk_reverse.setChecked(reverse)
        self.apply_params()
        self.input_U.clear(); self.input_I.clear(); self.input_P.clear()
        self.lbl_result.setText("Кездейсоқ таажрыйба түзүлдү.")

    def check(self):
        try:
            U_user = float(self.input_U.text())
            I_user = float(self.input_I.text())
            P_user = float(self.input_P.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "U, I жана P үчүн маанилерди киргизиңиз.")
            return
        U_true = self.motor.U
        I_true = self.motor.I
        P_true = U_true * I_true
        tol_U = 5
        tol_I = 0.1
        tol_P = 0.5
        ok_U = abs(U_user - U_true) <= tol_U
        ok_I = abs(I_user - I_true) <= tol_I
        ok_P = abs(P_user - P_true) <= tol_P
        lines = []
        if ok_U:
            lines.append("✅ U туура өлчөнүп алынды.")
        else:
            lines.append(f"❌ U (туура {U_true:.0f} V)")
        if ok_I:
            lines.append("✅ I туура өлчөнүп алынды.")
        else:
            lines.append(f"❌ I (туура {I_true:.2f} A)")
        if ok_P:
            lines.append("✅ P туура эсептелди.")
        else:
            lines.append(f"❌ P (туура {P_true:.1f} W)")
        self.lbl_result.setText("\n".join(lines))

    def show_answer(self):
        U = self.motor.U
        I = self.motor.I
        P = U * I
        self.input_U.setText(f"{U:.0f}")
        self.input_I.setText(f"{I:.2f}")
        self.input_P.setText(f"{P:.1f}")
        self.lbl_result.setText("Туура маанилер көрсөтүлдү.")

    def reset(self):
        self.slider_U.setValue(0)
        self.slider_I.setValue(0)
        self.chk_reverse.setChecked(False)
        self.apply_params()
        self.input_U.clear(); self.input_I.clear(); self.input_P.clear()
        self.lbl_result.setText("Сброшено.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabMotorApp()
    win.show()
    sys.exit(app.exec())
