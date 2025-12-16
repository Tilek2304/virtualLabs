import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox,
    QSlider, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QPainterPath
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF, Signal

# ==========================================
# КООЗ ПРИБОР (Стрелкалуу)
# ==========================================
class AnalogMeter(QFrame):
    def __init__(self, title, units, max_val, parent=None):
        super().__init__(parent)
        self.setMinimumSize(140, 140)
        self.title = title
        self.units = units
        self.max_val = max_val
        self.value = 0.0
        self.target_value = 0.0

    def set_value(self, val):
        self.target_value = val

    def update_needle(self):
        # Анимация
        diff = self.target_value - self.value
        self.value += diff * 0.15
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2 + 10
        r = min(w, h) / 2 - 10

        # Корпус
        p.setBrush(QColor(245, 245, 245))
        p.setPen(QPen(Qt.black, 2))
        p.drawEllipse(QPointF(cx, cy - 10), r, r)

        # Шкала
        p.setPen(QPen(Qt.black, 1))
        start_angle = 225
        span_angle = -90 # 90 градуска бурулат
        
        for i in range(11):
            val_norm = i / 10.0
            angle_deg = start_angle + val_norm * span_angle
            angle_rad = math.radians(angle_deg)
            
            p1 = QPointF(cx + (r-15)*math.cos(angle_rad), (cy-10) - (r-15)*math.sin(angle_rad))
            p2 = QPointF(cx + (r-5)*math.cos(angle_rad), (cy-10) - (r-5)*math.sin(angle_rad))
            p.drawLine(p1, p2)

        # Жазуулар
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.drawText(QRectF(cx - 30, cy + 10, 60, 20), Qt.AlignCenter, self.title)
        
        p.setFont(QFont("Arial", 12))
        p.setPen(QPen(QColor(0, 50, 150)))
        p.drawText(QRectF(cx - 30, cy - 40, 60, 20), Qt.AlignCenter, f"{self.value:.2f}")

        # Жебе
        val_clamped = max(0, min(self.value, self.max_val))
        ratio = val_clamped / self.max_val if self.max_val > 0 else 0
        needle_angle = start_angle + ratio * span_angle
        
        p.save()
        p.translate(cx, cy - 10)
        p.rotate(-needle_angle) # Qt айлануусу саат жебеси боюнча
        
        p.setPen(QPen(Qt.red, 3))
        p.drawLine(0, 0, 40, 0) # Жебе оңго карайт (айланганда туура болот)
        p.setBrush(Qt.black)
        p.drawEllipse(QPointF(0,0), 4, 4)
        p.restore()

# ==========================================
# ИНТЕРАКТИВДҮҮ СТЕНД
# ==========================================
class RealCircuitWidget(QFrame):
    loadChanged = Signal(float)
    switchToggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: #eef2f5; border: 1px solid #aaa; border-radius: 10px;")
        
        self.emf = 4.5
        self.r_int = 1.0
        self.r_load = 10.0
        self.is_closed = False
        
        self.is_dragging = False
        
        # Анимация таймери (жебелер үчүн)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        # Схеманын координаттары
        batt_x, batt_y = 100, 200
        res_x, res_y = 500, 200
        
        # 1. ЗЫМДАР (Калың)
        p.setPen(QPen(QColor(40, 40, 40), 4))
        p.setBrush(Qt.NoBrush)
        
        # Контур: Батарея -> Вольтметр -> Реостат -> Ачкыч -> Батарея
        path = QPainterPath()
        path.moveTo(batt_x, batt_y - 40) # Батареянын өйдө жагы
        path.lineTo(batt_x, 50)
        path.lineTo(res_x, 50)
        path.lineTo(res_x, batt_y - 80) # Реостаттын башы
        
        path.moveTo(res_x, batt_y + 80) # Реостаттын аягы
        path.lineTo(res_x, h - 50)
        path.lineTo(batt_x, h - 50)
        path.lineTo(batt_x, batt_y + 40)
        
        p.drawPath(path)
        
        # 2. БАТАРЕЯ
        p.setBrush(QColor(220, 220, 220))
        p.setPen(QPen(Qt.black, 2))
        p.drawRect(batt_x - 30, batt_y - 40, 60, 80)
        p.setFont(QFont("Arial", 12, QFont.Bold))
        p.drawText(batt_x - 10, batt_y + 5, "E, r")
        p.drawText(batt_x - 45, batt_y - 30, "+")
        p.drawText(batt_x - 45, batt_y + 40, "-")

        # 3. РЕОСТАТ (Слайдер)
        res_h = 160
        res_rect = QRectF(res_x - 15, batt_y - 80, 30, res_h)
        p.setBrush(QColor(160, 100, 50)) # Жыгач түс
        p.drawRect(res_rect)
        
        # Зым ороолору
        p.setPen(QPen(QColor(200, 200, 200), 1))
        for i in range(0, int(res_h), 4):
            p.drawLine(res_x - 15, batt_y - 80 + i, res_x + 15, batt_y - 80 + i)
            
        # Ползунок (Көк)
        # R = 1..20 Ом. 1 Ом = жогору, 20 Ом = ылдам
        # Формула: Y абалы R маанисине жараша
        # Төмөн (чоң R) -> Жогору (кичине R)
        # Физикалык реостатта: ток үстүнөн кирет, ползунок аркылуу чыгат.
        # Ползунок ылдый болсо = зым узун = R чоң.
        slider_ratio = (self.r_load - 1.0) / 19.0
        slider_y = (batt_y - 80) + slider_ratio * res_h
        
        self.slider_rect = QRectF(res_x - 25, slider_y - 10, 50, 20)
        p.setBrush(QColor(50, 100, 255))
        p.setPen(Qt.black)
        p.drawRoundedRect(self.slider_rect, 5, 5)
        p.setPen(Qt.white)
        p.drawText(self.slider_rect, Qt.AlignCenter, f"{self.r_load:.1f}Ω")

        # 4. АЧКЫЧ (Төмөндө)
        sw_x = 300
        sw_y = h - 50
        self.switch_rect = QRectF(sw_x - 30, sw_y - 20, 60, 40)
        
        p.setPen(QPen(Qt.black, 4))
        p.setBrush(Qt.black)
        p.drawEllipse(sw_x - 30, sw_y - 5, 10, 10)
        p.drawEllipse(sw_x + 20, sw_y - 5, 10, 10)
        
        p.setPen(QPen(QColor(80, 80, 80), 6))
        if self.is_closed:
            p.drawLine(sw_x - 30, sw_y, sw_x + 20, sw_y)
            status = "Жабык"
            col = QColor(0, 150, 0)
        else:
            p.drawLine(sw_x - 30, sw_y, sw_x + 10, sw_y - 30)
            status = "Ачык"
            col = QColor(200, 0, 0)
            
        p.setPen(col)
        p.drawText(sw_x - 20, sw_y - 30, status)

        # 5. ТОК БАГЫТЫ (Анимация)
        if self.is_closed:
            p.setPen(QPen(QColor(255, 200, 0, 180), 3))
            offset = (QApplication.activeWindow().frameGeometry().width() + event.rect().width()) % 20
            # Жөнөкөй визуалдаштыруу: зымдарды бойлой чекиттер
            # ... (татаал анимацияны жөнөкөйлөттүк)

    def mousePressEvent(self, event):
        if self.switch_rect.contains(event.position()):
            self.is_closed = not self.is_closed
            self.switchToggled.emit(self.is_closed)
            self.update()
        elif self.slider_rect.contains(event.position()):
            self.is_dragging = True

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            y = event.position().y()
            # Чектөөлөр (Реостаттын бийиктиги боюнча)
            top = 200 - 80
            bottom = 200 + 80
            y = max(top, min(bottom, y))
            
            # Y -> R (1ден 20го чейин)
            ratio = (y - top) / (bottom - top)
            new_r = 1.0 + ratio * 19.0
            
            self.r_load = new_r
            self.loadChanged.emit(new_r)
            self.update()

    def mouseReleaseEvent(self, event):
        self.is_dragging = False

class Lab17App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш №17: ЭКК жана Ички каршылык")
        self.resize(1100, 700)
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СОЛ: Приборлор жана Стенд ---
        left_layout = QVBoxLayout()
        
        # Приборлор (Амперметр, Вольтметр)
        meters = QHBoxLayout()
        self.ammeter = AnalogMeter("Амперметр", "A", 2.0) # Макс 2А
        self.voltmeter = AnalogMeter("Вольтметр", "V", 10.0) # Макс 10В
        meters.addWidget(self.ammeter)
        meters.addWidget(self.voltmeter)
        left_layout.addLayout(meters)
        
        # Схема
        self.circuit = RealCircuitWidget()
        self.circuit.loadChanged.connect(self.calc_physics)
        self.circuit.switchToggled.connect(self.calc_physics)
        left_layout.addWidget(self.circuit)
        
        main.addLayout(left_layout, 2)

        # --- ОҢ: Башкаруу жана Түшүндүрмө ---
        right_panel = QVBoxLayout()
        
        # 1. Формулалар (Түшүндүрмө)
        info_g = QGroupBox("Физикалык негиздеме")
        info_l = QVBoxLayout()
        info_l.addWidget(QLabel("<b>Ом мыйзамы (толук чынжыр):</b>"))
        self.lbl_formula_I = QLabel("I = E / (R + r)")
        self.lbl_formula_I.setStyleSheet("font-size: 14px; font-weight: bold; color: blue;")
        info_l.addWidget(self.lbl_formula_I)
        
        info_l.addWidget(QLabel("<b>Чыңалуу:</b>"))
        self.lbl_formula_U = QLabel("U = E - I * r")
        self.lbl_formula_U.setStyleSheet("font-size: 14px; font-weight: bold; color: darkred;")
        info_l.addWidget(self.lbl_formula_U)
        
        info_l.addWidget(QLabel("Эгер R көбөйсө -> I азаят -> U көбөйөт."))
        info_g.setLayout(info_l)
        right_panel.addWidget(info_g)

        # 2. Жыйынтыктарды жазуу
        calc_g = QGroupBox("Эсептөө")
        calc_l = QVBoxLayout()
        self.in_E = QLineEdit(); self.in_E.setPlaceholderText("E (Вольт) - ачык кезде")
        self.in_U = QLineEdit(); self.in_U.setPlaceholderText("U (Вольт) - жабык кезде")
        self.in_I = QLineEdit(); self.in_I.setPlaceholderText("I (Ампер) - жабык кезде")
        self.in_r = QLineEdit(); self.in_r.setPlaceholderText("r (Ом) - жыйынтык")
        
        calc_l.addWidget(self.in_E)
        calc_l.addWidget(self.in_U)
        calc_l.addWidget(self.in_I)
        calc_l.addWidget(self.in_r)
        
        btn_check = QPushButton("Текшерүү (r)")
        btn_check.clicked.connect(self.check_res)
        calc_l.addWidget(btn_check)
        
        btn_new = QPushButton("Жаңы эксперимент")
        btn_new.clicked.connect(self.new_experiment)
        calc_l.addWidget(btn_new)
        
        calc_g.setLayout(calc_l)
        right_panel.addWidget(calc_g)
        
        right_panel.addStretch(1)
        main.addLayout(right_panel, 1)
        
        # Таймер (приборлорду жаңыртуу үчүн)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_meters)
        self.timer.start(30)

    def new_experiment(self):
        self.emf = random.choice([4.5, 6.0, 9.0])
        self.r_int = random.uniform(0.5, 2.0)
        self.circuit.emf = self.emf
        self.circuit.r_int = self.r_int
        
        # Reset UI
        self.circuit.is_closed = False
        self.circuit.r_load = 10.0
        self.in_E.clear(); self.in_U.clear(); self.in_I.clear(); self.in_r.clear()
        self.calc_physics()
        
    def calc_physics(self):
        # Негизги физикалык эсептөө
        if not self.circuit.is_closed:
            # Ачык: I = 0, U = E
            self.current_I = 0.0
            self.current_U = self.emf
        else:
            # Жабык: I = E / (R + r)
            total_r = self.circuit.r_load + self.r_int
            self.current_I = self.emf / total_r
            # U = I * R
            self.current_U = self.current_I * self.circuit.r_load
            
        # Формулаларды жаңыртуу (көрсөтмө)
        self.lbl_formula_I.setText(f"I = {self.emf:.1f} / ({self.circuit.r_load:.1f} + {self.r_int:.1f}) = {self.current_I:.2f} A")
        self.lbl_formula_U.setText(f"U = {self.emf:.1f} - {self.current_I:.2f} * {self.r_int:.1f} = {self.current_U:.2f} V")

    def update_meters(self):
        self.ammeter.set_value(self.current_I)
        self.ammeter.update_needle()
        self.voltmeter.set_value(self.current_U)
        self.voltmeter.update_needle()

    def check_res(self):
        try:
            val = float(self.in_r.text())
            if abs(val - self.r_int) < 0.1:
                QMessageBox.information(self, "Туура", f"✅ r = {self.r_int:.2f} Ом")
            else:
                QMessageBox.warning(self, "Ката", "❌ Туура эмес.")
        except:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = Lab17App()
    win.show()
    sys.exit(app.exec())