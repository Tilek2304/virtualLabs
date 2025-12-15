# lab_resistance.py
# Требуется: pip install PySide6
import sys, random, math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt

class MeterWidget(QFrame):
    """
    Универсалдуу аналогдук прибор (A же V).
    """
    def __init__(self, kind="A", parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.kind = kind  # "A" же "V"
        self.value = 0.0
        self.max_display = 1.0

    def set_value(self, val, vmax=None):
        self.value = val if val is not None else 0.0
        if vmax is not None:
            self.max_display = max(1e-6, float(vmax))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        radius = min(w, h) // 2 - 8

        p.fillRect(self.rect(), QColor(250, 250, 250))
        p.setPen(QPen(Qt.black, 2))
        p.setBrush(QColor(255, 255, 255))
        p.drawEllipse(cx - radius, cy - radius, 2 * radius, 2 * radius)

        # Шкала
        p.setPen(QPen(Qt.black, 1))
        for angle in range(-60, 61, 10):
            rad = math.radians(angle)
            x0 = cx + int((radius - 8) * math.cos(rad))
            y0 = cy - int((radius - 8) * math.sin(rad))
            x1 = cx + int(radius * math.cos(rad))
            y1 = cy - int(radius * math.sin(rad))
            p.drawLine(x0, y0, x1, y1)

        # Жебе
        frac = 0.0
        if self.max_display > 0:
            frac = max(0.0, min(1.0, self.value / self.max_display))
        angle = -60 + frac * 120.0
        rad = math.radians(angle)
        p.setPen(QPen(QColor(200, 30, 30), 2))
        x_end = cx + int((radius - 14) * math.cos(rad))
        y_end = cy - int((radius - 14) * math.sin(rad))
        p.drawLine(cx, cy, x_end, y_end)

        # Текст
        p.setPen(QPen(Qt.black, 2))
        p.setFont(QFont("Sans", 12, QFont.Bold))
        p.drawText(cx - 10, cy + 6, self.kind)
        p.setFont(QFont("Sans", 9))
        if self.kind == "A":
            p.drawText(8, h - 10, f"{self.value:.3f} A / {self.max_display:.3f}")
        else:
            p.drawText(8, h - 10, f"{self.value:.2f} V / {self.max_display:.2f}")

class CircuitWidget(QFrame):
    """
    Туюк чынжыр: батарея, өткөргүч (R), амперметр жана вольтметр.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 360)
        self.U_source = 5.0
        self.R_sample = 10.0  # Ом
        self.R_internal = 1.0  # Ички каршылык
        self.I = None
        self.U_sample = None

    def set_params(self, U_source, R_sample, R_internal=1.0):
        self.U_source = float(U_source)
        self.R_sample = float(R_sample)
        self.R_internal = float(R_internal)
        self._recalc()
        self.update()

    def _recalc(self):
        R_total = self.R_sample + self.R_internal
        if R_total <= 1e-9:
            self.I = None
            self.U_sample = None
        else:
            self.I = self.U_source / R_total
            self.U_sample = self.I * self.R_sample

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(245, 245, 245))

        mid_y = h // 2
        left_x = 60
        right_x = w - 160

        # Батарея
        p.setPen(QPen(Qt.black, 2))
        p.setBrush(QColor(200, 200, 200))
        p.drawRect(left_x, mid_y - 18, 10, 36)
        p.setBrush(QColor(220, 220, 220))
        p.drawRect(left_x + 18, mid_y - 28, 10, 56)
        p.setPen(QPen(QColor(200, 30, 30), 3))
        p.drawLine(left_x + 28, mid_y, left_x + 100, mid_y)

        # Өткөргүч (резистор)
        x = left_x + 100
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(x, mid_y, x + 40, mid_y)
        sample_cx = x + 80
        p.setBrush(QColor(180, 180, 80))
        p.drawRect(sample_cx - 30, mid_y - 18, 60, 36)
        p.setFont(QFont("Sans", 10))
        # КОТОРМО: Rs = ...
        p.drawText(sample_cx - 22, mid_y + 4, f"Rs={self.R_sample:.1f}Ω")
        x = sample_cx + 30

        # Зым амперметрге чейин
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(x, mid_y, right_x, mid_y)

        # Амперметр (схематикалык)
        ax = right_x + 40
        ay = mid_y
        p.setBrush(QColor(255, 255, 255))
        p.setPen(QPen(Qt.black, 2))
        p.drawEllipse(ax - 36, ay - 36, 72, 72)
        p.setFont(QFont("Sans", 10))
        if self.I is not None:
            p.drawText(ax - 28, ay - 46, f"I = {self.I:.3f} A")
        else:
            p.drawText(ax - 28, ay - 46, "I = — A")

        # Чынжырды туташтыруу
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(ax + 36, ay, ax + 36, ay + 80)
        p.drawLine(ax + 36, ay + 80, left_x + 10, ay + 80)
        p.drawLine(left_x + 10, ay + 80, left_x + 10, mid_y - 6)
        p.drawLine(left_x + 10, mid_y - 6, left_x + 2, mid_y - 6)
        p.drawLine(left_x + 2, mid_y - 6, left_x + 2, mid_y + 6)
        p.drawLine(left_x + 2, mid_y + 6, left_x + 10, mid_y + 6)

        # Вольтметр (параллель)
        vx = sample_cx
        vy = mid_y - 90
        p.setBrush(QColor(255, 255, 255))
        p.setPen(QPen(Qt.black, 2))
        p.drawEllipse(vx - 28, vy - 28, 56, 56)
        p.setFont(QFont("Sans", 10))
        if self.U_sample is not None:
            p.drawText(vx - 24, vy - 36, f"Us={self.U_sample:.2f}V")
        else:
            p.drawText(vx - 24, vy - 36, "Us = — V")
        
        # Зымдар вольтметрге
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(sample_cx - 30, mid_y - 10, vx - 10, vy + 10)
        p.drawLine(sample_cx + 30, mid_y - 10, vx + 10, vy + 10)

        # Булак чыңалуусу
        p.setFont(QFont("Sans", 10))
        p.drawText(12, mid_y - 40, f"Uбулак = {self.U_source:.2f} В")

class LabResistanceApp(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Измерение сопротивления проводника -> Өткөргүчтүн каршылыгын өлчөө
        self.setWindowTitle("Лабораторная иш — Өткөргүчтүн каршылыгын өлчөө (R = U / I)")
        self.setMinimumSize(1000, 640)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.circuit = CircuitWidget()
        left.addWidget(self.circuit)

        # Жеке приборлор
        meters_row = QHBoxLayout()
        self.ammeter = MeterWidget("A")
        self.voltmeter = MeterWidget("V")
        meters_row.addWidget(self.ammeter)
        meters_row.addWidget(self.voltmeter)
        left.addLayout(meters_row)

        # Правая панель
        # КОТОРМО: Заголовок
        right.addWidget(QLabel("<b>Өткөргүчтүн каршылыгын өлчөө</b>"))
        
        # КОТОРМО: Инструкция
        info = QLabel(
            "Булактын чыңалуусун жана үлгү каршылыкты орнотуңуз.\n"
            "Чынжырды куруп, U жана I маанилерин өлчөп, R = U / I формуласы боюнча каршылыкты эсептеңиз."
        )
        info.setWordWrap(True)
        right.addWidget(info)

        # Параметрлер
        right.addWidget(QLabel("<b>Параметрлер</b>"))
        self.input_U = QLineEdit(); self.input_U.setPlaceholderText("U_булак (В)")
        self.input_Rs = QLineEdit(); self.input_Rs.setPlaceholderText("R_үлгү (Ом) — чыныгы маани")
        self.input_Rint = QLineEdit(); self.input_Rint.setPlaceholderText("R_ички (Ом) — милдеттүү эмес")
        
        right.addWidget(self.input_U)
        right.addWidget(self.input_Rs)
        right.addWidget(self.input_Rint)

        right.addSpacing(6)
        # КОТОРМО: Измерения и ответ -> Өлчөөлөр жана окуучунун жообу
        right.addWidget(QLabel("<b>Өлчөөлөр жана окуучунун жообу</b>"))
        self.input_Umeas = QLineEdit(); self.input_Umeas.setPlaceholderText("U (В) — вольтметр көрсөткөн")
        self.input_Imeas = QLineEdit(); self.input_Imeas.setPlaceholderText("I (А) — амперметр көрсөткөн")
        self.input_Ruser = QLineEdit(); self.input_Ruser.setPlaceholderText("R = U / I (Ом) — сиздин жооп")
        
        right.addWidget(self.input_Umeas)
        right.addWidget(self.input_Imeas)
        right.addWidget(self.input_Ruser)

        # Кнопки
        # КОТОРМО: Собрать цепь -> Чынжырды куруу
        btn_build = QPushButton("Чынжырды куруу")
        btn_build.clicked.connect(self.build)
        # КОТОРМО: Измерить -> Өлчөө (приборлорду көрүү)
        btn_measure = QPushButton("Өлчөө (приборлорду көрүү)")
        btn_measure.clicked.connect(self.measure)
        # КОТОРМО: Проверить R -> R текшерүү
        btn_check = QPushButton("R текшерүү")
        btn_check.clicked.connect(self.check_R)
        # КОТОРМО: Показать правильные значения -> Туура маанилерди көрсөтүү
        btn_show = QPushButton("Туура маанилерди көрсөтүү")
        btn_show.clicked.connect(self.show_answer)
        # КОТОРМО: Случайный эксперимент -> Кокустан тандалган тажрыйба
        btn_random = QPushButton("Кокустан тандалган тажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        # КОТОРМО: Сброс -> Кайра баштоо
        btn_reset = QPushButton("Кайра баштоо")
        btn_reset.clicked.connect(self.reset)

        right.addWidget(btn_build)
        right.addWidget(btn_measure)
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
            Rs = float(self.input_Rs.text())
            Rint = float(self.input_Rint.text()) if self.input_Rint.text().strip() else 1.0
        except Exception:
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "U жана R үчүн сан маанилерин киргизиңиз.")
            return
        self.circuit.set_params(U, Rs, Rint)
        self.ammeter.set_value(self.circuit.I if self.circuit.I is not None else 0.0, vmax=max(0.1, (self.circuit.U_source / max(1.0, Rs + Rint))))
        self.voltmeter.set_value(self.circuit.U_sample if self.circuit.U_sample is not None else 0.0, vmax=max(0.1, self.circuit.U_source))
        # КОТОРМО: Цепь собрана -> Чынжыр курулду
        self.lbl_result.setText("Чынжыр курулду. «Өлчөө» баскычын басып, приборлорду караңыз.")

    def measure(self):
        if self.circuit.I is None:
            QMessageBox.information(self, "Маалымат", "Адегенде чынжырды куруңуз.")
            return
        I_meas = self.circuit.I
        U_meas = self.circuit.U_sample
        self.ammeter.set_value(I_meas, vmax=max(0.1, (self.circuit.U_source / max(1.0, self.circuit.R_sample + self.circuit.R_internal))))
        self.voltmeter.set_value(U_meas, vmax=max(0.1, self.circuit.U_source))
        
        self.input_Umeas.setText(f"{U_meas:.3f}")
        self.input_Imeas.setText(f"{I_meas:.3f}")
        # КОТОРМО: Показания... -> Приборлордун көрсөткүчтөрү жаңырды
        self.lbl_result.setText("Приборлордун көрсөткүчтөрү жаңырды.")

    def check_R(self):
        try:
            U = float(self.input_Umeas.text())
            I = float(self.input_Imeas.text())
            R_user = float(self.input_Ruser.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "U, I жана R маанилерин киргизиңиз.")
            return
        if abs(I) < 1e-6:
            QMessageBox.information(self, "Маалымат", "Ток өтө аз.")
            return
        R_calc = U / I
        R_true = self.circuit.R_sample
        tol = max(0.03 * R_true, 0.05)
        ok = abs(R_user - R_calc) <= max(0.02 * R_calc, 0.01) and abs(R_calc - R_true) <= tol
        if ok:
            # КОТОРМО: ... верно -> ... туура эсептелди
            self.lbl_result.setText("✅ R туура эсептелди.")
        else:
            # КОТОРМО: Неверно -> Туура эмес
            self.lbl_result.setText(f"❌ Туура эмес. R_эсеп = {R_calc:.3f} Ω; туура R = {R_true:.3f} Ω ( piela ±{tol:.3f}).")

    def show_answer(self):
        if self.circuit.I is None:
            QMessageBox.information(self, "Маалымат", "Адегенде чынжырды куруңуз.")
            return
        U_meas = self.circuit.U_sample
        I_meas = self.circuit.I
        R_calc = U_meas / I_meas if abs(I_meas) > 1e-9 else 0.0
        self.input_Umeas.setText(f"{U_meas:.3f}")
        self.input_Imeas.setText(f"{I_meas:.3f}")
        self.input_Ruser.setText(f"{R_calc:.3f}")
        self.lbl_result.setText("Туура маанилер жана эсептөөлөр көрсөтүлдү.")

    def random_experiment(self):
        U = random.choice([3.0, 4.5, 6.0, 9.0, 12.0])
        R_sample = random.uniform(2.0, 50.0)
        R_int = random.uniform(0.5, 3.0)
        self.input_U.setText(f"{U:.1f}")
        self.input_Rs.setText(f"{R_sample:.2f}")
        self.input_Rint.setText(f"{R_int:.2f}")
        self.circuit.set_params(U, R_sample, R_int)
        
        self.ammeter.set_value(self.circuit.I if self.circuit.I is not None else 0.0, vmax=max(0.1, (self.circuit.U_source / max(1.0, R_sample + R_int))))
        self.voltmeter.set_value(self.circuit.U_sample if self.circuit.U_sample is not None else 0.0, vmax=max(0.1, self.circuit.U_source))
        
        self.input_Umeas.clear(); self.input_Imeas.clear(); self.input_Ruser.clear()
        self.lbl_result.setText("Жаңы тажрыйба түзүлдү.")

    def reset(self):
        self.input_U.clear(); self.input_Rs.clear(); self.input_Rint.clear()
        self.input_Umeas.clear(); self.input_Imeas.clear(); self.input_Ruser.clear()
        self.circuit.set_params(0.0, 10.0, 1.0)
        self.ammeter.set_value(0.0, vmax=1.0)
        self.voltmeter.set_value(0.0, vmax=5.0)
        self.lbl_result.setText("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabResistanceApp()
    win.show()
    sys.exit(app.exec())