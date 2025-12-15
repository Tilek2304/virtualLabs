# lab_current_series_improved.py
# Требуется: pip install PySide6
import sys, random, math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt

class CircuitWidget(QFrame):
    """
    Удаалаш туташтырылган чынжыр. Батарея, лампалар (каршылыктар)
    жана амперметр.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 360)
        self.U = 12.0
        self.resistors = [10.0, 10.0]  # Ом
        self.I = None
        self.update_current()

    def set_params(self, U, resistors):
        self.U = float(U)
        self.resistors = [float(r) for r in resistors]
        self.update_current()
        self.update()

    def update_current(self):
        R_total = sum(self.resistors) if self.resistors else 0.0
        self.I = (self.U / R_total) if R_total > 1e-9 else None

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))

        mid_y = h // 2
        left_x = 48
        right_x = w - 140

        # --- Батарея (сол жакта) ---
        p.setPen(QPen(Qt.black, 2))
        # кыска сызык (минус)
        p.setBrush(QColor(200,200,200))
        p.drawRect(left_x, mid_y - 18, 10, 36)
        # узун сызык (плюс)
        p.setBrush(QColor(220,220,220))
        p.drawRect(left_x + 18, mid_y - 28, 10, 56)
        # зым (кызыл)
        p.setPen(QPen(QColor(200,30,30), 3))
        p.drawLine(left_x + 28, mid_y, left_x + 90, mid_y)

        # --- Удаалаш лампалар / каршылыктар ---
        x = left_x + 90
        for i, R in enumerate(self.resistors):
            # зым
            p.setPen(QPen(Qt.black, 2))
            p.drawLine(x, mid_y, x + 30, mid_y)
            # лампа (сары тегерек)
            lamp_cx = x + 60
            lamp_cy = mid_y
            p.setBrush(QColor(255, 235, 120))
            p.setPen(QPen(Qt.black, 2))
            p.drawEllipse(lamp_cx - 22, lamp_cy - 22, 44, 44)
            # спираль
            p.setPen(QPen(Qt.black, 1))
            p.drawArc(lamp_cx - 14, lamp_cy - 10, 28, 20, 30 * 16, 220 * 16)
            # R мааниси
            p.setFont(QFont("Sans", 9))
            p.setPen(QPen(Qt.black, 1))
            p.drawText(lamp_cx - 18, lamp_cy + 36, f"R{i+1}={R:.0f}Ω")
            x = lamp_cx + 22

        # зым амперметрге чейин
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(x, mid_y, right_x, mid_y)

        # --- Амперметр (оң жакта, жогору) ---
        ax = right_x + 40
        ay = mid_y
        p.setBrush(QColor(255,255,255))
        p.setPen(QPen(Qt.black, 2))
        p.drawEllipse(ax - 36, ay - 36, 72, 72)

        # шкала
        p.setPen(QPen(Qt.black, 1))
        for angle in range(-60, 61, 15):
            rad = math.radians(angle)
            x1 = ax + 28 * math.cos(rad)
            y1 = ay - 28 * math.sin(rad)
            x0 = ax + 18 * math.cos(rad)
            y0 = ay - 18 * math.sin(rad)
            p.drawLine(x0, y0, x1, y1)

        # жебе (стрелка)
        if self.I is not None:
            R_total = sum(self.resistors)
            Imax = max(0.1, self.U / max(1.0, R_total * 0.6))
            frac = min(1.0, self.I / Imax)
            angle = -60 + frac * 120.0
            rad = math.radians(angle)
            p.setPen(QPen(QColor(200,30,30), 2))
            p.drawLine(ax, ay, ax + 26 * math.cos(rad), ay - 26 * math.sin(rad))
        else:
            rad = math.radians(-60)
            p.setPen(QPen(QColor(200,30,30), 2))
            p.drawLine(ax, ay, ax + 26 * math.cos(rad), ay - 26 * math.sin(rad))

        # тамга A жана мааниси
        p.setPen(QPen(Qt.black, 2))
        p.setFont(QFont("Sans", 12, QFont.Bold))
        p.drawText(ax - 8, ay + 6, "A")
        p.setFont(QFont("Sans", 10))
        if self.I is not None:
            p.drawText(ax - 30, ay - 46, f"I = {self.I:.3f} A")
        else:
            p.drawText(ax - 30, ay - 46, "I = — A")

        # --- туташтыруу (төмөнкү бөлүк) ---
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(ax + 36, ay, ax + 36, ay + 80)
        p.drawLine(ax + 36, ay + 80, left_x + 10, ay + 80)
        p.drawLine(left_x + 10, ay + 80, left_x + 10, mid_y - 6)
        p.drawLine(left_x + 10, mid_y - 6, left_x + 2, mid_y - 6)
        p.drawLine(left_x + 2, mid_y - 6, left_x + 2, mid_y + 6)
        p.drawLine(left_x + 2, mid_y + 6, left_x + 10, mid_y + 6)
        
        # Чыңалуунун мааниси
        p.setFont(QFont("Sans", 9))
        p.drawText(12, mid_y - 40, f"U = {self.U:.1f} В")

class LabCurrentImprovedApp(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Сила тока в последовательной цепи -> Удаалаш туташтырылган чынжырдагы ток күчү
        self.setWindowTitle("Лабораториялык иш — Удаалаш туташтырылган чынжырдагы ток күчү")
        self.setMinimumSize(1000, 640)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.circuit = CircuitWidget()
        left.addWidget(self.circuit)

        # КОТОРМО: Заголовок
        right.addWidget(QLabel("<b>Удаалаш туташтырылган чынжырдагы ток күчү</b>"))
        
        # КОТОРМО: Инструкция
        info = QLabel(
            "Ток булагынын чыңалуусун жана удаалаш туташтырылган лампалардын каршылыгын киргизиңиз.\n"
            "Чынжырды куруп, ток күчү бардык бөлүктөрдө бирдей экенин текшериңиз: I = U / (R1+R2+...)."
        )
        info.setWordWrap(True)
        right.addWidget(info)

        self.input_U = QLineEdit(); self.input_U.setPlaceholderText("U (В)")
        # КОТОРМО: Сопротивления через запятую -> Каршылыктарды үтүр аркылуу
        self.input_Rs = QLineEdit(); self.input_Rs.setPlaceholderText("Каршылыктар (Ом), мисалы: 10,15,20")
        self.input_I = QLineEdit(); self.input_I.setPlaceholderText("I (А) — сиздин жооп")
        
        right.addWidget(self.input_U)
        right.addWidget(self.input_Rs)
        right.addWidget(self.input_I)

        # Кнопки
        # КОТОРМО: Собрать цепь -> Чынжырды куруу
        btn_build = QPushButton("Чынжырды куруу")
        btn_build.clicked.connect(self.build)
        
        # КОТОРМО: Проверить -> Текшерүү
        btn_check = QPushButton("Текшерүү")
        btn_check.clicked.connect(self.check)
        
        # КОТОРМО: Показать ответ -> Жоопту көрсөтүү
        btn_show = QPushButton("Жоопту көрсөтүү")
        btn_show.clicked.connect(self.show_answer)
        
        # КОТОРМО: Случайный эксперимент -> Кокустан тандалган тажрыйба
        btn_random = QPushButton("Кокустан тандалган тажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        
        # КОТОРМО: Сброс -> Кайра баштоо
        btn_reset = QPushButton("Кайра баштоо")
        btn_reset.clicked.connect(self.reset)

        right.addWidget(btn_build)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        self.lbl_result = QLabel("")
        right.addWidget(self.lbl_result)
        right.addStretch(1)

        self.random_experiment()

    def build(self):
        try:
            U = float(self.input_U.text())
            Rs = [float(x.strip()) for x in self.input_Rs.text().split(",") if x.strip() != ""]
            if not Rs:
                raise ValueError
        except Exception:
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "Чыңалууну (U) жана каршылыктардын тизмесин туура киргизиңиз.")
            return
        self.circuit.set_params(U, Rs)
        # КОТОРМО: Цепь собрана -> Чынжыр курулду
        self.lbl_result.setText("Чынжыр курулду. Амперметрди карап, I маанисин эсептеңиз.")

    def check(self):
        if self.circuit.I is None:
            # КОТОРМО: Инфо -> Маалымат
            QMessageBox.information(self, "Маалымат", "Адегенде чынжырды куруңуз.")
            return
        try:
            I_user = float(self.input_I.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "I маанисин сан түрүндө киргизиңиз.")
            return
        I_true = self.circuit.I
        tol = max(0.05 * abs(I_true), 0.005)
        if abs(I_user - I_true) <= tol:
            # КОТОРМО: Ответ верный -> Жооп туура
            self.lbl_result.setText("✅ Жооп туура.")
        else:
            # КОТОРМО: Неверно -> Туура эмес
            self.lbl_result.setText(f"❌ Туура эмес. Туура I = {I_true:.3f} А ( piela ±{tol:.3f}).")

    def show_answer(self):
        if self.circuit.I is None:
            QMessageBox.information(self, "Маалымат", "Адегенде чынжырды куруңуз.")
            return
        self.input_I.setText(f"{self.circuit.I:.3f}")
        # КОТОРМО: Показан правильный ответ -> Туура жооп көрсөтүлдү
        self.lbl_result.setText("Туура жооп көрсөтүлдү.")

    def random_experiment(self):
        U = random.randint(6, 18)
        n = random.choice([2, 3])
        Rs = [random.randint(5, 30) for _ in range(n)]
        self.input_U.setText(str(U))
        self.input_Rs.setText(",".join(str(r) for r in Rs))
        self.circuit.set_params(U, Rs)
        self.input_I.clear()
        self.lbl_result.setText("Жаңы тажрыйба даярдалды.")

    def reset(self):
        self.input_U.clear()
        self.input_Rs.clear()
        self.input_I.clear()
        self.circuit.set_params(0.0, [10.0, 10.0])
        self.lbl_result.setText("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabCurrentImprovedApp()
    win.show()
    sys.exit(app.exec())