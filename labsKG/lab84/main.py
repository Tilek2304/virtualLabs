# lab_rheostat.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt

class CircuitWidget(QFrame):
    """
    Батарея — реостат — амперметр. Туюк чынжыр. Аналогдук амперметр.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 340)
        self.U = 12.0         # В
        self.R_fixed = 10.0   # Ом (туруктуу резистор/лампа)
        self.R_rheo = 20.0    # Ом (реостат)
        self.I = self.compute_current()

    def set_params(self, U, R_fixed):
        self.U = float(U)
        self.R_fixed = max(0.0, float(R_fixed))
        self.I = self.compute_current()
        self.update()

    def set_rheo(self, R_rheo):
        self.R_rheo = max(0.0, float(R_rheo))
        self.I = self.compute_current()
        self.update()

    def compute_current(self):
        R_total = self.R_fixed + self.R_rheo
        return (self.U / R_total) if R_total > 0 else 0.0

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        mid_y = h // 2
        p.fillRect(self.rect(), QColor(245, 245, 245))

        # Батарея
        p.setPen(QPen(Qt.black, 2))
        p.setBrush(QColor(200, 200, 200))
        p.drawRect(40, mid_y - 20, 10, 40)   # кыска
        p.setBrush(QColor(220, 220, 220))
        p.drawRect(55, mid_y - 30, 10, 60)   # узун
        p.setPen(QPen(Qt.red, 3))
        p.drawLine(65, mid_y, 110, mid_y)

        # Реостат (жылдыргыч)
        base_x = 110
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(base_x, mid_y, base_x + 40, mid_y)
        # Жол
        p.setBrush(QColor(180, 180, 80))
        p.setPen(QPen(Qt.black, 2))
        p.drawRoundedRect(base_x + 40, mid_y - 18, 80, 36, 6, 6)
        # Жылдыргыч (абалы R_rheo-го жараша)
        norm = max(0.0, min(1.0, self.R_rheo / 100.0))
        knob_x = int(base_x + 46 + norm * 68)
        p.setBrush(QColor(80, 120, 180))
        p.drawRoundedRect(knob_x - 6, mid_y - 22, 12, 44, 3, 3)
        p.setFont(QFont("Sans", 9))
        # КОТОРМО: Реостат
        p.drawText(base_x + 42, mid_y - 24, "Реостат")
        p.drawText(base_x + 42, mid_y + 32, f"R={self.R_rheo:.1f} Ω")

        # Зым амперметрге чейин
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(base_x + 120, mid_y, w - 140, mid_y)

        # Амперметр
        ax, ay = w - 100, mid_y
        p.setBrush(QColor(255, 255, 255))
        p.setPen(QPen(Qt.black, 2))
        p.drawEllipse(ax - 30, ay - 30, 60, 60)
        # Шкала
        p.setPen(QPen(Qt.black, 1))
        for angle in range(-60, 61, 15):
            rad = math.radians(angle)
            x1 = ax + 24 * math.cos(rad)
            y1 = ay - 24 * math.sin(rad)
            x0 = ax + 18 * math.cos(rad)
            y0 = ay - 18 * math.sin(rad)
            p.drawLine(x0, y0, x1, y1)
        # Жебе
        Imax = max(0.1, self.U / max(1.0, self.R_fixed + 1.0))
        angle = -60 + max(0.0, min(120.0, (self.I / Imax) * 120.0))
        rad = math.radians(angle)
        p.setPen(QPen(Qt.red, 2))
        p.drawLine(ax, ay, ax + 22 * math.cos(rad), ay - 22 * math.sin(rad))
        # Белгилер
        p.setPen(QPen(Qt.black, 2))
        p.setFont(QFont("Sans", 12, QFont.Bold))
        p.drawText(ax - 7, ay + 6, "A")
        p.setFont(QFont("Sans", 10))
        p.drawText(ax - 26, ay - 40, f"I={self.I:.2f} A")

        # Чынжырды туташтыруу (ылдый жана кайра)
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(ax + 30, ay, ax + 30, ay + 80)
        p.drawLine(ax + 30, ay + 80, 40, ay + 80)
        p.drawLine(40, ay + 80, 40, mid_y)

        # Rфикс мааниси
        p.setFont(QFont("Sans", 10))
        # КОТОРМО: Rфикс -> Rтурук
        p.drawText(40, mid_y - 50, f"U={self.U:.1f} В, Rтурук={self.R_fixed:.1f} Ω")

class LabRheostatApp(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Регулирование силы тока реостатом -> Ток күчүн реостат менен жөнгө салуу
        self.setWindowTitle("Лабораторная иш — Ток күчүн реостат менен жөнгө салуу")
        self.setMinimumSize(980, 560)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.circuit = CircuitWidget()
        left.addWidget(self.circuit)

        # Правая панель
        # КОТОРМО: Заголовок
        right.addWidget(QLabel("<b>Ток күчүн реостат менен жөнгө салуу</b>"))
        
        # КОТОРМО: Инструкция
        info = QLabel("Реостаттын жылдыргычын жылдырып, I(R) көз карандылыгын байкаңыз.\n"
                      "Ом мыйзамы: I = U / (Rтурук + Rрео).")
        info.setWordWrap(True)
        right.addWidget(info)

        self.input_U = QLineEdit(); self.input_U.setPlaceholderText("U (В)")
        self.input_Rfixed = QLineEdit(); self.input_Rfixed.setPlaceholderText("R турук (Ом)")
        right.addWidget(self.input_U)
        right.addWidget(self.input_Rfixed)

        # КОТОРМО: Реостат
        right.addWidget(QLabel("<b>Реостат</b>"))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0); self.slider.setMaximum(100); self.slider.setValue(20)
        self.slider.valueChanged.connect(self.on_slider)
        right.addWidget(self.slider)

        self.input_I = QLineEdit(); self.input_I.setPlaceholderText("I (А) — сиздин жооп")
        right.addWidget(self.input_I)

        # Кнопки
        # КОТОРМО: Применить -> Параметрлерди колдонуу
        btn_apply = QPushButton("Параметрлерди колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        # КОТОРМО: Проверить I -> I текшерүү
        btn_check = QPushButton("I текшерүү")
        btn_check.clicked.connect(self.check_I)
        # КОТОРМО: Показать I -> I көрсөтүү
        btn_show = QPushButton("I көрсөтүү")
        btn_show.clicked.connect(self.show_I)
        # КОТОРМО: Случайный эксперимент -> Кокустан тандалган тажрыйба
        btn_random = QPushButton("Кокустан тандалган тажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        # КОТОРМО: Сброс -> Кайра баштоо
        btn_reset = QPushButton("Кайра баштоо")
        btn_reset.clicked.connect(self.reset)

        right.addWidget(btn_apply)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        self.lbl_result = QLabel("")
        right.addWidget(self.lbl_result)
        right.addStretch(1)

        self.random_experiment()

    def on_slider(self, val):
        self.circuit.set_rheo(val)

    def apply_params(self):
        try:
            U = float(self.input_U.text())
            Rf = float(self.input_Rfixed.text())
        except Exception:
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "U жана R турук үчүн сан маанилерин киргизиңиз.")
            return
        self.circuit.set_params(U, Rf)

    def check_I(self):
        try:
            I_user = float(self.input_I.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "I маанисин сан түрүндө киргизиңиз.")
            return
        I_true = self.circuit.I
        tol = max(0.05 * I_true, 0.01)
        if abs(I_user - I_true) <= tol:
            # КОТОРМО: ... верно -> ... туура
            self.lbl_result.setText("✅ I туура эсептелди.")
        else:
            # КОТОРМО: Неверно -> Туура эмес
            self.lbl_result.setText(f"❌ Туура эмес. Туура I ≈ {I_true:.3f} А ( piela ±{tol:.3f}).")

    def show_I(self):
        self.input_I.setText(f"{self.circuit.I:.3f}")
        # КОТОРМО: Показано -> Көрсөтүлдү
        self.lbl_result.setText("Туура I көрсөтүлдү.")

    def random_experiment(self):
        U = random.randint(6, 18)
        Rf = random.randint(5, 30)
        Rr = random.randint(5, 80)
        self.input_U.setText(str(U))
        self.input_Rfixed.setText(str(Rf))
        self.slider.setValue(Rr)
        self.circuit.set_params(U, Rf)
        self.circuit.set_rheo(Rr)
        self.input_I.clear()
        self.lbl_result.setText("Жаңы тажрыйба даярдалды.")

    def reset(self):
        self.input_U.clear(); self.input_Rfixed.clear(); self.input_I.clear()
        self.slider.setValue(20)
        self.circuit.set_params(12.0, 10.0)
        self.circuit.set_rheo(20.0)
        self.lbl_result.setText("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabRheostatApp()
    win.show()
    sys.exit(app.exec())