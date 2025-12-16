import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSlider
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QRadialGradient, QLinearGradient
from PySide6.QtCore import Qt, QTimer, QPointF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Катушка жана Амперметр
# ==========================================
class CoilWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 400)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")
        
        # Параметрлер
        self.L = 0.5    # Индуктивдүүлүк (Гн)
        self.I_ind = 0.0 # Индукциялык ток
        
        # Анимация
        self.needle_angle = 0.0
        self.target_angle = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(20)

    def trigger_pulse(self, emf, resistance):
        # Импульс берүү: I = E / R
        if resistance <= 0: resistance = 1e-6
        current = emf / resistance
        
        # Жебенин бурчу (максимум +/- 60 градус)
        # 1 мА = 60 градус (сезгичтик)
        angle = current * 60000 
        if angle > 60: angle = 60
        if angle < -60: angle = -60
        
        self.needle_angle = angle # Кескин секирүү
        self.target_angle = 0.0   # Кайра нөлгө умтулуу

    def animate(self):
        # Жебени жайлап нөлгө түшүрүү (демпинг)
        diff = self.target_angle - self.needle_angle
        self.needle_angle += diff * 0.1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        # 1. Катушка (Схематикалык сүрөт)
        coil_x = cx - 180
        coil_y = cy - 50
        coil_w = 120
        coil_h = 100
        
        # Өзөк
        painter.setBrush(QColor(150, 150, 150))
        painter.setPen(Qt.black)
        painter.drawRect(coil_x, coil_y + 20, coil_w, 60)
        
        # Ороолор
        painter.setPen(QPen(QColor(184, 115, 51), 3))
        painter.setBrush(Qt.NoBrush)
        for i in range(8):
            x = coil_x + 10 + i * 14
            painter.drawEllipse(x, coil_y + 10, 14, 80)
            
        # Зымдар
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(coil_x, coil_y + 50, coil_x - 30, coil_y + 50)
        painter.drawLine(coil_x + coil_w, coil_y + 50, cx, coil_y + 50) # Амперметрге

        # 2. Миллиамперметр
        meter_x = cx + 80
        meter_y = cy
        meter_r = 80
        
        # Корпус
        painter.setBrush(QColor(240, 240, 240))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawEllipse(QPointF(meter_x, meter_y), meter_r, meter_r)
        
        # Шкала
        painter.setPen(QPen(Qt.black, 1))
        for i in range(-60, 61, 10):
            ang_rad = math.radians(i - 90)
            x1 = meter_x + (meter_r - 10) * math.cos(ang_rad)
            y1 = meter_y + (meter_r - 10) * math.sin(ang_rad)
            x2 = meter_x + (meter_r - 5) * math.cos(ang_rad)
            y2 = meter_y + (meter_r - 5) * math.sin(ang_rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            
        painter.drawText(meter_x - 10, meter_y + 40, "mA")
        
        # Жебе
        painter.save()
        painter.translate(meter_x, meter_y)
        painter.rotate(self.needle_angle)
        painter.setPen(QPen(Qt.red, 2))
        painter.drawLine(0, 0, 0, -meter_r + 15)
        painter.setBrush(Qt.black)
        painter.drawEllipse(QPointF(0,0), 3, 3)
        painter.restore()
        
        # Байланыш зымдары
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(meter_x - meter_r, meter_y, cx, meter_y) # Катушкадан
        painter.drawLine(meter_x + meter_r, meter_y, w - 20, meter_y) # Чыгыш

# ==========================================
# НЕГИЗГИ ТЕРЕЗЕ
# ==========================================
class LabInductanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш №14: Индуктивдүүлүк")
        self.resize(1000, 600)
        
        self.L_true = 0.5 # Гн
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СОЛ ЖАК: Стенд ---
        left_group = QGroupBox("Тажрыйба стенди")
        left_layout = QVBoxLayout()
        self.coil = CoilWidget()
        left_layout.addWidget(self.coil)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- ОҢ ЖАК: Башкаруу ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Тапшырма
        task_g = QGroupBox("Тапшырма")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. Токтун өзгөрүүсүн (ΔI) жана убакытты (Δt) киргизиңиз."))
        task_l.addWidget(QLabel("2. 'Өзгөртүү' баскычын басып, ЭКК (E) маанисин алыңыз."))
        task_l.addWidget(QLabel("3. Индуктивдүүлүктү табыңыз: L = |E| * Δt / ΔI."))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Параметрлер
        ctrl_g = QGroupBox("Башкаруу")
        ctrl_l = QVBoxLayout()
        
        self.in_dI = QLineEdit(); self.in_dI.setPlaceholderText("ΔI (Ампер)")
        self.in_dt = QLineEdit(); self.in_dt.setPlaceholderText("Δt (секунд)")
        self.in_R = QLineEdit("100"); self.in_R.setPlaceholderText("Каршылык R (Ом)")
        
        btn_pulse = QPushButton("Токту өзгөртүү (Импульс)")
        btn_pulse.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        btn_pulse.clicked.connect(self.trigger_pulse)
        
        ctrl_l.addWidget(QLabel("Токтун өзгөрүүсү ΔI (A):"))
        ctrl_l.addWidget(self.in_dI)
        ctrl_l.addWidget(QLabel("Убакыт Δt (с):"))
        ctrl_l.addWidget(self.in_dt)
        ctrl_l.addWidget(QLabel("Чынжырдын каршылыгы R (Ом):"))
        ctrl_l.addWidget(self.in_R)
        ctrl_l.addWidget(btn_pulse)
        
        ctrl_g.setLayout(ctrl_l)
        right_panel.addWidget(ctrl_g)

        # 3. Жыйынтык
        res_g = QGroupBox("Жыйынтык")
        res_l = QVBoxLayout()
        
        self.lbl_emf = QLabel("ЭКК (E) = 0.00 В")
        self.lbl_emf.setStyleSheet("font-weight: bold; color: blue;")
        
        self.in_L = QLineEdit(); self.in_L.setPlaceholderText("Индуктивдүүлүк L (Гн)")
        
        btn_check = QPushButton("Текшерүү")
        btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_check.clicked.connect(self.check_answer)
        
        btn_new = QPushButton("Жаңы эксперимент")
        btn_new.clicked.connect(self.new_experiment)
        
        res_l.addWidget(self.lbl_emf)
        res_l.addWidget(self.in_L)
        res_l.addWidget(btn_check)
        res_l.addWidget(btn_new)
        
        res_g.setLayout(res_l)
        right_panel.addWidget(res_g)
        
        right_panel.addStretch(1)

    def new_experiment(self):
        self.L_true = random.uniform(0.1, 2.0) # 0.1ден 2.0 Гн чейин
        self.coil.L = self.L_true
        
        self.in_dI.clear()
        self.in_dt.setText("0.1")
        self.in_L.clear()
        self.lbl_emf.setText("ЭКК (E) = 0.00 В")
        
        QMessageBox.information(self, "Тапшырма", "Жаңы катушка берилди (L өзгөрдү).")

    def trigger_pulse(self):
        try:
            dI = float(self.in_dI.text())
            dt = float(self.in_dt.text())
            R = float(self.in_R.text())
        except:
            QMessageBox.warning(self, "Ката", "Сандарды туура киргизиңиз!")
            return
            
        if dt <= 0:
            QMessageBox.warning(self, "Ката", "Убакыт нөлдөн чоң болушу керек!")
            return

        # Эсептөө: E = -L * dI / dt
        E = -self.L_true * (dI / dt)
        
        self.lbl_emf.setText(f"ЭКК (E) = {abs(E):.4f} В")
        self.coil.trigger_pulse(E, R)

    def check_answer(self):
        try:
            u_L = float(self.in_L.text())
        except:
            return
            
        if abs(u_L - self.L_true) < 0.05:
            QMessageBox.information(self, "Туура", f"✅ Азаматсыз! L = {self.L_true:.3f} Гн")
        else:
            QMessageBox.warning(self, "Ката", "❌ Туура эмес. Формуланы текшериңиз.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabInductanceApp()
    win.show()
    sys.exit(app.exec())