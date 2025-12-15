# lab_inductance.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer

class CoilWidget(QFrame):
    """Катушка жана микроамперметр."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 300)
        # Моделдин параметрлери
        self.I_now = 0.0
        self.I_prev = 0.0
        self.L_true = 0.05  # Чыныгы индуктивдүүлүк (Гн)
        self.E_ind = 0.0
        self.I_ind = 0.0
        self.R_load = 10.0

    def set_state(self, I_now=None, I_prev=None, L_true=None, E_ind=None, I_ind=None, R_load=None):
        if I_now is not None: self.I_now = float(I_now)
        if I_prev is not None: self.I_prev = float(I_prev)
        if L_true is not None: self.L_true = float(L_true)
        if E_ind is not None: self.E_ind = float(E_ind)
        if I_ind is not None: self.I_ind = float(I_ind)
        if R_load is not None: self.R_load = float(R_load)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250, 250, 250))

        cx = w // 2
        top = 40

        # Катушка (көрүнүшү)
        coil_x = cx - 160
        coil_y = top + 20
        coil_w = 120
        coil_h = 220
        p.setPen(QPen(Qt.black, 2))
        p.setBrush(QColor(230, 220, 200))
        p.drawRoundedRect(coil_x, coil_y, coil_w, coil_h, 8, 8)

        # Ороолор (витки)
        p.setPen(QPen(QColor(120, 60, 20), 2))
        turns = 12
        for i in range(turns):
            t = i / max(1, turns - 1)
            y = coil_y + 8 + t * (coil_h - 16)
            p.drawArc(coil_x + 6, int(y) - 8, coil_w - 12, 16, 0, 180 * 16)

        # Индуктивдүүлүк (жашырылган)
        p.setFont(QFont("Sans", 10))
        p.setPen(QPen(Qt.black, 1))
        # КОТОРМО: L (модель) -> L (чыныгы)
        p.drawText(coil_x + 6, coil_y - 6, f"L (чыныгы) = {self.L_true:.4f} Гн")

        # Зымдар
        load_x = cx + 80
        load_y = top + 80
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(coil_x + coil_w, coil_y + coil_h // 2, load_x - 20, coil_y + coil_h // 2)

        # Нагрузка (резистор)
        p.setBrush(QColor(200, 200, 200))
        p.drawRect(load_x - 20, load_y - 10, 60, 20)
        p.setFont(QFont("Sans", 9))
        p.setPen(QPen(Qt.black, 1))
        p.drawText(load_x - 8, load_y + 6, "R")

        # Амперметр (микроамперметр)
        ax = load_x + 80
        ay = load_y
        p.setBrush(QColor(255, 255, 255))
        p.setPen(QPen(Qt.black, 2))
        p.drawEllipse(ax - 28, ay - 28, 56, 56)
        p.setFont(QFont("Sans", 10, QFont.Bold))
        p.drawText(ax - 8, ay + 6, "μA")
        p.setFont(QFont("Sans", 9))
        p.drawText(ax - 36, ay + 36, f"I_ind = {self.I_ind*1e6:.1f} μA")

        # Жебе
        Imax = max(1e-6, max(abs(self.I_ind), 1e-6) * 10)
        frac = max(-1.0, min(1.0, self.I_ind / Imax))
        angle = -60 + (frac + 1) * 60  # -60..60
        rad = math.radians(angle)
        p.setPen(QPen(QColor(200, 30, 30), 2))
        p.drawLine(ax, ay, int(ax + 20 * math.cos(rad)), int(ay - 20 * math.sin(rad)))

        # Токтордун маанилери
        p.setPen(QPen(Qt.black, 1))
        p.drawText(12, h - 40, f"I_азыр = {self.I_now:.3f} A")
        p.drawText(12, h - 22, f"I_мурда = {self.I_prev:.3f} A")
        p.drawText(220, h - 40, f"E_ind = {self.E_ind*1e3:.3f} mV")
        p.drawText(220, h - 22, f"R_load = {self.R_load:.1f} Ω")

class LabInductanceApp(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Индуктивность катушки -> Катушканын индуктивдүүлүгүн аныктоо
        self.setWindowTitle("Лабораториялык иш — Катушканын индуктивдүүлүгүн аныктоо")
        self.setMinimumSize(1000, 520)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.coil_widget = CoilWidget()
        left.addWidget(self.coil_widget)

        # Правая панель
        # КОТОРМО: Заголовок
        right.addWidget(QLabel("<b>Тажрыйбанын параметрлери</b>"))
        
        self.input_L_true = QLineEdit(); self.input_L_true.setPlaceholderText("L (Гн) — кааласаңыз киргизиңиз")
        self.input_I1 = QLineEdit(); self.input_I1.setPlaceholderText("I1 (A) — баштапкы ток")
        self.input_I2 = QLineEdit(); self.input_I2.setPlaceholderText("I2 (A) — акыркы ток")
        self.input_dt = QLineEdit(); self.input_dt.setPlaceholderText("Δt (с) — убакыт")
        self.input_R = QLineEdit(); self.input_R.setPlaceholderText("R (Ω) — каршылык")
        
        right.addWidget(self.input_L_true)
        right.addWidget(self.input_I1)
        right.addWidget(self.input_I2)
        right.addWidget(self.input_dt)
        right.addWidget(self.input_R)

        right.addSpacing(6)
        # КОТОРМО: Поля ученика -> Окуучунун эсептөөлөрү
        right.addWidget(QLabel("<b>Окуучунун эсептөөлөрү</b>"))
        self.input_E_meas = QLineEdit(); self.input_E_meas.setPlaceholderText("E (В) — индукциялык ЭКК")
        self.input_di = QLineEdit(); self.input_di.setPlaceholderText("ΔI (A) — токтун өзгөрүшү (I2−I1)")
        self.input_dt_meas = QLineEdit(); self.input_dt_meas.setPlaceholderText("Δt (с) — убакыт")
        self.input_L_user = QLineEdit(); self.input_L_user.setPlaceholderText("L (Гн) — сиздин эсептөөңүз")
        
        right.addWidget(self.input_E_meas)
        right.addWidget(self.input_di)
        right.addWidget(self.input_dt_meas)
        right.addWidget(self.input_L_user)

        # Кнопки
        # КОТОРМО: Применить параметры -> Параметрлерди колдонуу
        btn_apply = QPushButton("Параметрлерди колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        # КОТОРМО: Изменить ток -> Токту өзгөртүү (ΔI симуляциясы)
        btn_change = QPushButton("Токту өзгөртүү (ΔI симуляциясы)")
        btn_change.clicked.connect(self.change_current)
        # КОТОРМО: Измерить -> Өлчөө (көрсөткүчтөрдү алуу)
        btn_measure = QPushButton("Өлчөө (көрсөткүчтөрдү алуу)")
        btn_measure.clicked.connect(self.measure)
        # КОТОРМО: Проверить L -> L текшерүү
        btn_check = QPushButton("L текшерүү")
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

        right.addWidget(btn_apply)
        right.addWidget(btn_change)
        right.addWidget(btn_measure)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        right.addSpacing(8)
        # КОТОРМО: Результаты -> Жыйынтыктар
        right.addWidget(QLabel("<b>Жыйынтыктар</b>"))
        self.lbl_E = QLabel("E_ind: — V")
        self.lbl_Iind = QLabel("I_ind: — A")
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setWordWrap(True)
        right.addWidget(self.lbl_E)
        right.addWidget(self.lbl_Iind)
        right.addWidget(self.lbl_feedback)
        right.addStretch(1)

        self.random_experiment()

    def apply_params(self):
        try:
            L = float(self.input_L_true.text()) if self.input_L_true.text().strip() else self.coil_widget.L_true
            I1 = float(self.input_I1.text())
            I2 = float(self.input_I2.text())
            dt = float(self.input_dt.text())
            R = float(self.input_R.text())
        except Exception:
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "Бардык параметрлерди сан түрүндө киргизиңиз.")
            return
        self.coil_widget.set_state(I_now=I2, I_prev=I1, L_true=L, R_load=R)
        # КОТОРМО: Параметры применены -> Параметрлер колдонулду
        self.lbl_feedback.setText("Параметрлер колдонулду. «Токту өзгөртүү» баскычын басыңыз.")
        self.update_labels()

    def change_current(self):
        try:
            I1 = float(self.input_I1.text())
            I2 = float(self.input_I2.text())
            dt = float(self.input_dt.text())
            R = float(self.input_R.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "Параметрлерди текшериңиз.")
            return
        L = self.coil_widget.L_true
        dI = I2 - I1
        E = - L * (dI / dt)
        I_ind = 0.0
        if abs(R) > 1e-9:
            I_ind = E / R
        self.coil_widget.set_state(I_now=I2, I_prev=I1, E_ind=E, I_ind=I_ind, R_load=R)
        # КОТОРМО: Симуляция... -> Ток өзгөрдү. Эми «Өлчөө» баскычын басыңыз.
        self.lbl_feedback.setText("Ток өзгөрдү. Эми «Өлчөө» баскычын басыңыз.")
        self.update_labels()

    def measure(self):
        E = self.coil_widget.E_ind
        dI = self.coil_widget.I_now - self.coil_widget.I_prev
        dt = float(self.input_dt.text()) if self.input_dt.text().strip() else 0.01
        
        if E is None:
            QMessageBox.information(self, "Маалымат", "Адегенде токту өзгөртүңүз.")
            return
        
        E_meas = E * (1 + random.uniform(-0.02, 0.02))
        dI_meas = dI * (1 + random.uniform(-0.01, 0.01))
        dt_meas = dt * (1 + random.uniform(-0.01, 0.01))
        
        self.input_E_meas.setText(f"{E_meas:.6f}")
        self.input_di.setText(f"{dI_meas:.6f}")
        self.input_dt_meas.setText(f"{dt_meas:.6f}")
        
        # КОТОРМО: Поля заполнены -> Көрсөткүчтөр жазылды (кичине ката менен).
        self.lbl_feedback.setText("Көрсөткүчтөр жазылды (кичине ката менен).")
        self.update_labels()

    def check(self):
        try:
            E_user = float(self.input_E_meas.text())
            dI_user = float(self.input_di.text())
            dt_user = float(self.input_dt_meas.text())
            L_user = float(self.input_L_user.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "Бардык талааларды толтуруңуз.")
            return
        
        if abs(dI_user) < 1e-9:
            QMessageBox.information(self, "Маалымат", "ΔI өтө аз.")
            return
            
        L_calc = - E_user * dt_user / dI_user
        L_true = self.coil_widget.L_true
        tol = max(0.03 * abs(L_true), 1e-6)
        
        ok_calc = abs(L_user - L_calc) <= max(0.02 * abs(L_calc), 1e-6)
        ok_true = abs(L_calc - L_true) <= tol
        
        lines = []
        if ok_calc:
            lines.append("✅ Сиздин L эсебиңиз өлчөөлөргө туура келет.")
        else:
            lines.append(f"❌ Сиздин L эсебиңиз ката. L_эсеп = {L_calc:.6f} Гн.")
        
        if ok_true:
            lines.append("✅ Өлчөө чыныгы мааниге жакын.")
        else:
            lines.append(f"❌ Өлчөө чыныгы мааниден айырмаланат: L_чыныгы = {L_true:.6f} Гн.")
            
        self.lbl_feedback.setText("\n".join(lines))

    def show_answer(self):
        L_true = self.coil_widget.L_true
        dI = self.coil_widget.I_now - self.coil_widget.I_prev
        dt = float(self.input_dt.text()) if self.input_dt.text().strip() else float(self.input_dt_meas.text() or 0.01)
        
        if abs(dI) < 1e-9:
            QMessageBox.information(self, "Маалымат", "ΔI өтө аз же жок.")
            return
            
        E = self.coil_widget.E_ind
        L_calc = - E * dt / dI
        
        self.input_E_meas.setText(f"{E:.6f}")
        self.input_di.setText(f"{dI:.6f}")
        self.input_dt_meas.setText(f"{dt:.6f}")
        self.input_L_user.setText(f"{L_calc:.6f}")
        self.lbl_feedback.setText("Туура маанилер көрсөтүлдү.")
        self.update_labels()

    def random_experiment(self):
        L = random.uniform(1e-4, 5e-2)  # Гн
        I1 = random.uniform(0.0, 0.5)
        I2 = I1 + random.uniform(0.01, 0.5)
        dt = random.uniform(0.005, 0.1)
        R = random.choice([10.0, 20.0, 50.0, 100.0])
        
        self.input_L_true.setText(f"{L:.6f}")
        self.input_I1.setText(f"{I1:.3f}")
        self.input_I2.setText(f"{I2:.3f}")
        self.input_dt.setText(f"{dt:.4f}")
        self.input_R.setText(f"{R:.1f}")
        
        self.coil_widget.set_state(I_now=I2, I_prev=I1, L_true=L, R_load=R)
        self.change_current()
        
        self.input_E_meas.clear(); self.input_di.clear(); self.input_dt_meas.clear(); self.input_L_user.clear()
        self.lbl_feedback.setText("Жаңы тажрыйба даярдалды. «Өлчөө» баскычын басыңыз же өзүңүз киргизиңиз.")
        self.update_labels()

    def reset(self):
        self.input_L_true.clear(); self.input_I1.clear(); self.input_I2.clear()
        self.input_dt.clear(); self.input_R.clear()
        self.input_E_meas.clear(); self.input_di.clear(); self.input_dt_meas.clear(); self.input_L_user.clear()
        self.coil_widget.set_state(I_now=0.0, I_prev=0.0, L_true=0.05, E_ind=0.0, I_ind=0.0, R_load=10.0)
        self.lbl_feedback.setText("Тазаланды.")
        self.update_labels()

    def update_labels(self):
        self.lbl_E.setText(f"E_ind: {self.coil_widget.E_ind:.6f} V")
        self.lbl_Iind.setText(f"I_ind: {self.coil_widget.I_ind:.6e} A")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabInductanceApp()
    win.show()
    sys.exit(app.exec())