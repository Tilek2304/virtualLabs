# lab_rheostat.py
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt

class CircuitWidget(QFrame):
    """
    Батарея — реостат — амперметр. Замкнутая схема. Красивый аналоговый амперметр.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 340)
        self.U = 12.0         # В
        self.R_fixed = 10.0   # Ом (постоянный резистор/лампа)
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
        mid_y = h//2
        p.fillRect(self.rect(), QColor(245,245,245))

        # батарея
        p.setPen(QPen(Qt.black,2))
        p.setBrush(QColor(200,200,200))
        p.drawRect(40, mid_y-20, 10, 40)   # короткий
        p.setBrush(QColor(220,220,220))
        p.drawRect(55, mid_y-30, 10, 60)   # длинный
        p.setPen(QPen(Qt.red,3))
        p.drawLine(65, mid_y, 110, mid_y)

        # реостат (ползунок резистивной дорожки)
        base_x = 110
        p.setPen(QPen(Qt.black,2))
        p.drawLine(base_x, mid_y, base_x+40, mid_y)
        # дорожка
        p.setBrush(QColor(180,180,80))
        p.setPen(QPen(Qt.black,2))
        p.drawRoundedRect(base_x+40, mid_y-18, 80, 36, 6, 6)
        # ползунок (позиция визуально пропорциональна R_rheo)
        # нормируем R_rheo к [0, 1] относительно 0..100 Ом визуально
        norm = max(0.0, min(1.0, self.R_rheo / 100.0))
        knob_x = int(base_x+46 + norm * 68)
        p.setBrush(QColor(80,120,180))
        p.drawRoundedRect(knob_x-6, mid_y-22, 12, 44, 3, 3)
        p.setFont(QFont("Sans",9))
        p.drawText(base_x+42, mid_y-24, "Реостат")
        p.drawText(base_x+42, mid_y+32, f"R={self.R_rheo:.1f} Ω")

        # провод к амперметру
        p.setPen(QPen(Qt.black,2))
        p.drawLine(base_x+120, mid_y, w-140, mid_y)

        # амперметр (круглый прибор со шкалой и стрелкой)
        ax, ay = w-100, mid_y
        p.setBrush(QColor(255,255,255))
        p.setPen(QPen(Qt.black,2))
        p.drawEllipse(ax-30, ay-30, 60, 60)
        # шкала
        p.setPen(QPen(Qt.black,1))
        for angle in range(-60, 61, 15):
            rad = math.radians(angle)
            x1 = ax + 24*math.cos(rad)
            y1 = ay - 24*math.sin(rad)
            x0 = ax + 18*math.cos(rad)
            y0 = ay - 18*math.sin(rad)
            p.drawLine(x0, y0, x1, y1)
        # стрелка: масштабируем ток к углу [-60..60] при диапазоне 0..Imax
        Imax = max(0.1, self.U / max(1.0, self.R_fixed + 1.0))  # приблизительная шкала
        angle = -60 + max(0.0, min(120.0, (self.I / Imax) * 120.0))
        rad = math.radians(angle)
        p.setPen(QPen(Qt.red,2))
        p.drawLine(ax, ay, ax + 22*math.cos(rad), ay - 22*math.sin(rad))
        # метки
        p.setPen(QPen(Qt.black,2))
        p.setFont(QFont("Sans",12, QFont.Bold))
        p.drawText(ax-7, ay+6, "A")
        p.setFont(QFont("Sans",10))
        p.drawText(ax-26, ay-40, f"I={self.I:.2f} A")

        # замыкание цепи вниз и обратно
        p.setPen(QPen(Qt.black,2))
        p.drawLine(ax+30, ay, ax+30, ay+80)      # вниз от амперметра
        p.drawLine(ax+30, ay+80, 40, ay+80)      # влево
        p.drawLine(40, ay+80, 40, mid_y)         # вверх к батарее

        # подпись фикс. резистора
        p.setFont(QFont("Sans",10))
        p.drawText(40, mid_y-50, f"U={self.U:.1f} В, Rфикс={self.R_fixed:.1f} Ω")

class LabRheostatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная — Регулирование силы тока реостатом")
        self.setMinimumSize(980, 560)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.circuit = CircuitWidget()
        left.addWidget(self.circuit)

        # правая панель
        right.addWidget(QLabel("<b>Регулирование силы тока реостатом</b>"))
        info = QLabel("Двигайте ползунок реостата и наблюдайте зависимость I(R).\n"
                      "Закон Ома: I = U / (Rфикс + Rрео).")
        info.setWordWrap(True)
        right.addWidget(info)

        self.input_U = QLineEdit(); self.input_U.setPlaceholderText("U (В)")
        self.input_Rfixed = QLineEdit(); self.input_Rfixed.setPlaceholderText("R фикс (Ом)")
        right.addWidget(self.input_U)
        right.addWidget(self.input_Rfixed)

        # слайдер реостата (0..100 Ом)
        right.addWidget(QLabel("<b>Реостат</b>"))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0); self.slider.setMaximum(100); self.slider.setValue(20)
        self.slider.valueChanged.connect(self.on_slider)
        right.addWidget(self.slider)

        # поле для ответа ученика (например: пара точек или ток при текущем R)
        self.input_I = QLineEdit(); self.input_I.setPlaceholderText("I (А) — ваш расчёт при текущем R")
        right.addWidget(self.input_I)

        btn_apply = QPushButton("Применить U и Rфикс")
        btn_apply.clicked.connect(self.apply_params)
        btn_check = QPushButton("Проверить I")
        btn_check.clicked.connect(self.check_I)
        btn_show = QPushButton("Показать I")
        btn_show.clicked.connect(self.show_I)
        btn_random = QPushButton("Случайный эксперимент")
        btn_random.clicked.connect(self.random_experiment)
        btn_reset = QPushButton("Сброс")
        btn_reset.clicked.connect(self.reset)

        right.addWidget(btn_apply)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        self.lbl_result = QLabel("")
        right.addWidget(self.lbl_result)
        right.addStretch(1)

        # стартовые значения
        self.random_experiment()

    def on_slider(self, val):
        self.circuit.set_rheo(val)

    def apply_params(self):
        try:
            U = float(self.input_U.text())
            Rf = float(self.input_Rfixed.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения U и R фикс.")
            return
        self.circuit.set_params(U, Rf)

    def check_I(self):
        try:
            I_user = float(self.input_I.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовое значение I.")
            return
        I_true = self.circuit.I
        tol = max(0.05 * I_true, 0.01)
        if abs(I_user - I_true) <= tol:
            self.lbl_result.setText("✅ I рассчитано верно.")
        else:
            self.lbl_result.setText(f"❌ Неверно. Правильное I ≈ {I_true:.3f} А (допуск ±{tol:.3f}).")

    def show_I(self):
        self.input_I.setText(f"{self.circuit.I:.3f}")
        self.lbl_result.setText("Показано правильное I при текущем R.")

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
        self.lbl_result.setText("Сгенерирован новый эксперимент.")

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
