# lab_internal_resistance.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer

# Универсалдуу аналогдук прибор
class MeterWidget(QFrame):
    def __init__(self, kind="A", parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.kind = kind
        self.value = 0.0
        self.max_display = 1.0

    def set_value(self, val, vmax=None):
        self.value = val if val is not None else 0.0
        if vmax is not None:
            self.max_display = max(1e-9, float(vmax))
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
        if abs(self.value) < 1e-6:
            p.drawText(8, h-10, "0.00")
        else:
            p.drawText(8, h-10, f"{self.value:.4g}")

# Батарея + реостат
class BatteryWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(720, 360)
        # Параметрлер
        self.E = 1.5        # ЭКК, В
        self.r = 0.5        # ички каршылык, Ом
        self.R = 10.0       # тышкы жүк, Ом
        self._recompute()

    def set_params(self, E=None, r=None, R=None):
        if E is not None: self.E = float(E)
        if r is not None: self.r = float(r)
        if R is not None: self.R = float(R)
        self._recompute()
        self.update()

    def _recompute(self):
        denom = self.r + self.R
        if abs(denom) < 1e-12:
            self.I = 0.0
        else:
            self.I = self.E / denom
        self.U = self.E - self.I * self.r

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))
        cx = w // 2
        top = 40

        # Батарея
        bat_x = cx - 220
        bat_y = top + 40
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(240,220,220))
        p.drawRoundedRect(bat_x, bat_y, 120, 120, 8, 8)
        p.setFont(QFont("Sans",10,QFont.Bold)); p.setPen(QPen(Qt.black,1))
        # КОТОРМО: Battery -> Батарея
        p.drawText(bat_x + 18, bat_y + 64, "Батарея")
        p.drawText(bat_x + 12, bat_y + 88, f"E = {self.E:.3f} В")

        # Реостат
        load_x = cx + 80
        load_y = top + 80
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(220,240,220))
        p.drawRect(load_x - 20, load_y - 20, 120, 40)
        p.setFont(QFont("Sans",10)); p.setPen(QPen(Qt.black,1))
        p.drawText(load_x + 6, load_y + 6, f"R = {self.R:.2f} Ω")

        # Зымдар
        p.setPen(QPen(Qt.black, 3))
        p.drawLine(bat_x + 120, bat_y + 60, load_x - 20, bat_y + 60)
        p.drawLine(load_x + 100, load_y, load_x + 100, load_y + 60)
        p.drawLine(load_x + 100, load_y + 60, bat_x + 60, load_y + 60)
        p.drawLine(bat_x + 60, load_y + 60, bat_x + 60, bat_y + 120)

        # Амперметр
        am_x = bat_x + 20; am_y = load_y + 60
        p.setBrush(QColor(255,255,255)); p.setPen(QPen(Qt.black,2))
        p.drawEllipse(am_x - 24, am_y - 24, 48, 48)
        p.setFont(QFont("Sans",9,QFont.Bold)); p.drawText(am_x - 8, am_y + 6, "A")
        p.setFont(QFont("Sans",9)); p.drawText(am_x - 36, am_y + 36, f"I = {self.I:.4f} A")

        # Вольтметр
        v_x = load_x + 60; v_y = load_y - 60
        p.setBrush(QColor(255,255,255)); p.setPen(QPen(Qt.black,2))
        p.drawEllipse(v_x - 24, v_y - 24, 48, 48)
        p.setFont(QFont("Sans",9,QFont.Bold)); p.drawText(v_x - 10, v_y + 6, "V")
        p.setFont(QFont("Sans",9)); p.drawText(v_x - 36, v_y + 36, f"U = {self.U:.3f} В")

        # Текст
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",10))
        p.drawText(12, 18, f"E (модель) = {self.E:.3f} В")
        p.drawText(12, 36, f"r (модель) = {self.r:.3f} Ω")
        p.drawText(12, 54, f"R (жүк) = {self.R:.3f} Ω")
        p.drawText(12, 72, f"I (модель) = {self.I:.4f} A")
        p.drawText(12, 90, f"U (модель) = {self.U:.3f} В")

class LabInternalResApp(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: ЭДС и внутреннее сопротивление источника -> Ток булагынын ЭККсын жана ички каршылыгын аныктоо
        self.setWindowTitle("Лабораториялык иш — Ток булагынын ЭККсын жана ички каршылыгын аныктоо")
        self.setMinimumSize(1100, 700)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.batt_widget = BatteryWidget()
        left.addWidget(self.batt_widget)

        meters = QHBoxLayout()
        self.ammeter = MeterWidget("A")
        self.voltmeter = MeterWidget("V")
        meters.addWidget(self.ammeter); meters.addWidget(self.voltmeter)
        left.addLayout(meters)

        # Правая панель
        # КОТОРМО: Заголовок
        right.addWidget(QLabel("<b>Ток булагынын параметрлери</b>"))
        self.input_E = QLineEdit(); self.input_E.setPlaceholderText("E (В) — ЭКК (милдеттүү эмес)")
        self.input_r = QLineEdit(); self.input_r.setPlaceholderText("r (Ω) — ички каршылык")
        self.input_R = QLineEdit(); self.input_R.setPlaceholderText("R (Ω) — тышкы жүк")
        right.addWidget(self.input_E); right.addWidget(self.input_r); right.addWidget(self.input_R)

        right.addSpacing(6)
        # КОТОРМО: Управление нагрузкой -> Жүктү башкаруу (Реостат)
        right.addWidget(QLabel("<b>Жүктү башкаруу (Реостат)</b>"))
        self.slider_R = QSlider(Qt.Horizontal)
        self.slider_R.setRange(1, 500)
        self.slider_R.setValue(int(self.batt_widget.R))
        self.slider_R.valueChanged.connect(self.on_slider_R)
        right.addWidget(self.slider_R)
        self.lbl_R = QLabel(f"R = {self.batt_widget.R:.1f} Ω")
        right.addWidget(self.lbl_R)

        right.addSpacing(6)
        # КОТОРМО: Режим -> Режим
        right.addWidget(QLabel("<b>Режим</b>"))
        self.chk_manual = QCheckBox("Кол менен жазуу (авто толтуруу жок)")
        right.addWidget(self.chk_manual)

        right.addSpacing(6)
        # КОТОРМО: Поля ученика -> Окуучунун эсептөөлөрү
        right.addWidget(QLabel("<b>Окуучунун эсептөөлөрү</b>"))
        self.input_E_meas = QLineEdit(); self.input_E_meas.setPlaceholderText("E (В) — өлчөнгөн ЭКК")
        self.input_U_meas = QLineEdit(); self.input_U_meas.setPlaceholderText("U (В) — чыңалуу")
        self.input_I_meas = QLineEdit(); self.input_I_meas.setPlaceholderText("I (A) — ток")
        self.input_r_user = QLineEdit(); self.input_r_user.setPlaceholderText("r (Ω) — сиздин эсептөө")
        right.addWidget(self.input_E_meas)
        right.addWidget(self.input_U_meas)
        right.addWidget(self.input_I_meas)
        right.addWidget(self.input_r_user)

        # Кнопки
        # КОТОРМО: Применить -> Колдонуу
        btn_apply = QPushButton("Колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        # КОТОРМО: Измерить E (разомкнутая) -> ЭККны өлчөө (чынжыр ачык)
        btn_open = QPushButton("ЭККны өлчөө (чынжыр ачык)")
        btn_open.clicked.connect(self.measure_open)
        # КОТОРМО: Измерить при нагрузке -> Жүк менен өлчөө
        btn_load = QPushButton("Жүк менен өлчөө")
        btn_load.clicked.connect(self.measure_load)
        # КОТОРМО: Проверить r -> r текшерүү
        btn_check = QPushButton("r текшерүү")
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
        right.addWidget(btn_open)
        right.addWidget(btn_load)
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
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(200)

    def on_slider_R(self, val):
        R = float(val)
        self.lbl_R.setText(f"R = {R:.1f} Ω")
        self.batt_widget.set_params(R=R)
        self._update_ui()

    def apply_params(self):
        try:
            E = float(self.input_E.text()) if self.input_E.text().strip() else self.batt_widget.E
            r = float(self.input_r.text()) if self.input_r.text().strip() else self.batt_widget.r
            R = float(self.input_R.text()) if self.input_R.text().strip() else self.batt_widget.R
        except Exception:
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "E, r жана R үчүн сан маанилерин киргизиңиз.")
            return
        self.batt_widget.set_params(E=E, r=r, R=R)
        self.slider_R.setValue(int(R))
        # КОТОРМО: Параметры применены -> Параметрлер колдонулду
        self.lbl_feedback.setText("Параметрлер колдонулду. ЭККны же жүктөгү маанилерди өлчөңүз.")
        self._update_ui()

    def measure_open(self):
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Кол режими: талаалар автоматтык толтурулбайт.")
            return
        E_meas = self.batt_widget.E * (1 + random.uniform(-0.005, 0.005))
        self.input_E_meas.setText(f"{E_meas:.4f}")
        # КОТОРМО: Измерение... -> ЭКК өлчөндү.
        self.lbl_feedback.setText("ЭКК өлчөндү.")
        self._update_ui()

    def measure_load(self):
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Кол режими: талаалар автоматтык толтурулбайт.")
            return
        self.batt_widget._recompute()
        U = self.batt_widget.U
        I = self.batt_widget.I
        U_meas = U * (1 + random.uniform(-0.02, 0.02))
        I_meas = I * (1 + random.uniform(-0.02, 0.02))
        self.input_U_meas.setText(f"{U_meas:.4f}")
        self.input_I_meas.setText(f"{I_meas:.6f}")
        # КОТОРМО: Измерение... -> Жүк менен өлчөө аяктады.
        self.lbl_feedback.setText("Жүк менен өлчөө аяктады.")
        self._update_ui()

    def check(self):
        try:
            E_user = float(self.input_E_meas.text())
            U_user = float(self.input_U_meas.text())
            I_user = float(self.input_I_meas.text())
            r_user = float(self.input_r_user.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "Бардык талааларды толтуруңуз.")
            return
        if abs(I_user) < 1e-9:
            QMessageBox.information(self, "Маалымат", "Ток өтө аз.")
            return
        r_calc = (E_user - U_user) / I_user
        r_true = self.batt_widget.r
        tol_calc = max(0.03 * abs(r_calc), 1e-4)
        tol_true = max(0.05 * abs(r_true), 1e-4)
        ok_user = abs(r_user - r_calc) <= tol_calc
        ok_model = abs(r_calc - r_true) <= tol_true
        lines = []
        if ok_user:
            lines.append("✅ Сиздин r эсебиңиз туура.")
        else:
            lines.append(f"❌ Сиздин r эсебиңиз ката. r_эсеп = {r_calc:.6f} Ω.")
        if ok_model:
            lines.append("✅ Чыныгы мааниге жакын.")
        else:
            lines.append(f"❌ Чыныгы мааниден айырмаланат: r = {r_true:.6f} Ω ( piela ±{tol_true:.6f}).")
        self.lbl_feedback.setText("\n".join(lines))
        self._update_ui()

    def show_answer(self):
        E = self.batt_widget.E
        self.batt_widget._recompute()
        U = self.batt_widget.U
        I = self.batt_widget.I
        if abs(I) < 1e-12:
            QMessageBox.information(self, "Маалымат", "Ток өтө аз.")
            return
        r_calc = (E - U) / I
        self.input_E_meas.setText(f"{E:.4f}")
        self.input_U_meas.setText(f"{U:.4f}")
        self.input_I_meas.setText(f"{I:.6f}")
        self.input_r_user.setText(f"{r_calc:.6f}")
        self.lbl_feedback.setText("Туура маанилер көрсөтүлдү.")
        self._update_ui()

    def random_experiment(self):
        E = random.choice([1.5, 3.0, 4.5, 6.0, 9.0, 12.0])
        r = random.uniform(0.05, 2.0)
        R = random.uniform(1.0, 200.0)
        self.input_E.setText(f"{E:.3f}")
        self.input_r.setText(f"{r:.3f}")
        self.input_R.setText(f"{R:.2f}")
        self.batt_widget.set_params(E=E, r=r, R=R)
        self.slider_R.setValue(int(R))
        self.input_E_meas.clear(); self.input_U_meas.clear(); self.input_I_meas.clear(); self.input_r_user.clear()
        self.lbl_feedback.setText("Жаңы тажрыйба даярдалды.")
        self._update_ui()

    def reset_all(self):
        self.input_E.clear(); self.input_r.clear(); self.input_R.clear()
        self.input_E_meas.clear(); self.input_U_meas.clear(); self.input_I_meas.clear(); self.input_r_user.clear()
        self.batt_widget.set_params(E=1.5, r=0.5, R=10.0)
        self.slider_R.setValue(int(self.batt_widget.R))
        self.lbl_feedback.setText("Тазаланды.")
        self._update_ui()

    def _update_ui(self):
        self.batt_widget._recompute()
        self.ammeter.set_value(self.batt_widget.I, vmax=max(1e-6, abs(self.batt_widget.I)*2))
        self.voltmeter.set_value(self.batt_widget.U, vmax=max(1e-3, abs(self.batt_widget.U)*2))
        self.lbl_model.setText(f"Модель: E={self.batt_widget.E:.3f} В, r={self.batt_widget.r:.3f} Ω, R={self.batt_widget.R:.2f} Ω")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabInternalResApp()
    win.show()
    sys.exit(app.exec())