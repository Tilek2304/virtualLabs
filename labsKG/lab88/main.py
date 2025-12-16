import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox, QSpinBox, QGroupBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QRadialGradient, QLinearGradient
from PySide6.QtCore import Qt, QTimer, QPointF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Электромагнит жана Компас
# ==========================================
class ElectromagnetWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 400)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")
        
        # Параметрлер
        self.I = 0.0        # Ток, Ампер
        self.N = 50         # Ороолордун саны
        self.has_core = False # Темир өзөк барбы?
        
        # Анимация жана бурч
        self.current_angle = 0.0
        self.target_angle = 0.0
        self.mag_field_strength = 0.0 # Визуалдык эффект үчүн
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(20)

    def set_params(self, I, N, has_core):
        self.I = I
        self.N = N
        self.has_core = has_core
        self.calc_physics()
        self.update()

    def calc_physics(self):
        # Магнит талаасынын индукциясы: B ~ mu * N * I
        mu = 5.0 if self.has_core else 1.0 # Темир өзөк талааны 5 эсе күчөтөт (шарттуу)
        B = mu * self.N * self.I
        
        self.mag_field_strength = min(1.0, B / 1000.0) # Эффект үчүн нормалдаштыруу
        
        # Компастын бурулуусу (максимум 90 градус)
        # Tanh функциясы менен чектейбиз
        self.target_angle = 90 * math.tanh(B / 500.0)

    def animate(self):
        diff = self.target_angle - self.current_angle
        if abs(diff) > 0.1:
            self.current_angle += diff * 0.1
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        # 1. Катушка (Соленоид)
        coil_x = cx - 150
        coil_y = cy
        coil_w = 120
        coil_h = 60
        
        # Өзөк (Эгер бар болсо)
        if self.has_core:
            painter.setBrush(QColor(100, 100, 100)) # Темир түс
            painter.setPen(Qt.NoPen)
            painter.drawRect(coil_x - 10, coil_y - 20, coil_w + 20, 40)
            
        # Ороолор (Зым)
        painter.setPen(QPen(QColor(184, 115, 51), 3)) # Жез түс
        painter.setBrush(Qt.NoBrush)
        
        turns = min(20, self.N // 5) # Визуалдык ороолор
        step = coil_w / turns
        
        for i in range(turns):
            x = coil_x + i * step
            # Спираль эффекти
            painter.drawArc(int(x), int(coil_y - 30), int(step), 60, 0, 180 * 16)
            
        # Зымдардын учтары (Ток булагына кеткен)
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(coil_x, coil_y + 30, coil_x, h - 20)
        painter.drawLine(coil_x + coil_w, coil_y + 30, coil_x + coil_w, h - 20)
        
        # Магниттик талаанын сызыктары (Эгер ток бар болсо)
        if self.mag_field_strength > 0.01:
            alpha = int(self.mag_field_strength * 200)
            painter.setPen(QPen(QColor(0, 0, 255, alpha), 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            # Эллипстер аркылуу талааны көрсөтүү
            for i in range(1, 4):
                margin = i * 40
                painter.drawEllipse(coil_x - margin, coil_y - 30 - margin/2, 
                                  coil_w + 2*margin, 60 + margin)

        # 2. Компас
        comp_x = cx + 100
        comp_y = cy
        comp_r = 50
        
        # Корпус
        painter.setBrush(QColor(240, 240, 240))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawEllipse(QPointF(comp_x, comp_y), comp_r, comp_r)
        
        # Белгилер (N, S, W, E)
        painter.setFont(QFont("Arial", 8))
        painter.drawText(comp_x - 5, comp_y - 35, "N")
        painter.drawText(comp_x - 5, comp_y + 45, "S")
        
        # Жебе (Стрелка)
        painter.save()
        painter.translate(comp_x, comp_y)
        painter.rotate(self.current_angle)
        
        # Түндүк (Кызыл)
        painter.setBrush(QColor(255, 0, 0))
        painter.setPen(Qt.NoPen)
        arrow_n = [QPointF(-5, 0), QPointF(5, 0), QPointF(0, -40)]
        painter.drawPolygon(arrow_n)
        
        # Түштүк (Көк)
        painter.setBrush(QColor(0, 0, 255))
        arrow_s = [QPointF(-5, 0), QPointF(5, 0), QPointF(0, 40)]
        painter.drawPolygon(arrow_s)
        
        # Борбор
        painter.setBrush(Qt.black)
        painter.drawEllipse(QPointF(0, 0), 3, 3)
        
        painter.restore()
        
        # Бурчту жазуу
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(comp_x - 20, comp_y + 70, f"{self.current_angle:.1f}°")

# ==========================================
# НЕГИЗГИ ТЕРЕЗЕ
# ==========================================
class LabElectromagnetApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш №12: Электромагнит")
        self.resize(1000, 600)
        self.setup_ui()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СОЛ ЖАК: Стенд ---
        left_group = QGroupBox("Тажрыйба стенди")
        left_layout = QVBoxLayout()
        self.magnet = ElectromagnetWidget()
        left_layout.addWidget(self.magnet)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- ОҢ ЖАК: Башкаруу ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Тапшырма
        task_g = QGroupBox("Тапшырма")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. Токтун күчүн (I) өзгөртүңүз."))
        task_l.addWidget(QLabel("2. Ороолордун санын (N) өзгөртүңүз."))
        task_l.addWidget(QLabel("3. Темир өзөктү салып, айырманы байкаңыз."))
        task_l.addWidget(QLabel("Максат: Магнит талаасынын күчү эмнеден көз каранды экенин аныктоо."))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Башкаруу
        ctrl_g = QGroupBox("Параметрлер")
        ctrl_l = QVBoxLayout()
        
        # Ток (Слайдер)
        ctrl_l.addWidget(QLabel("Ток күчү (I):"))
        self.slider_I = QSlider(Qt.Horizontal)
        self.slider_I.setRange(0, 500) # 0.00 -> 5.00 A
        self.slider_I.setValue(0)
        self.slider_I.valueChanged.connect(self.update_params)
        self.lbl_I = QLabel("0.00 А")
        h_I = QHBoxLayout()
        h_I.addWidget(self.slider_I)
        h_I.addWidget(self.lbl_I)
        ctrl_l.addLayout(h_I)
        
        # Ороолор (SpinBox)
        ctrl_l.addWidget(QLabel("Ороолордун саны (N):"))
        self.spin_N = QSpinBox()
        self.spin_N.setRange(10, 500)
        self.spin_N.setValue(50)
        self.spin_N.setSingleStep(10)
        self.spin_N.valueChanged.connect(self.update_params)
        ctrl_l.addWidget(self.spin_N)
        
        # Темир өзөк (CheckBox)
        self.chk_core = QCheckBox("Темир өзөк (Сердечник)")
        self.chk_core.stateChanged.connect(self.update_params)
        ctrl_l.addWidget(self.chk_core)
        
        ctrl_g.setLayout(ctrl_l)
        right_panel.addWidget(ctrl_g)

        # 3. Жыйынтык жазуу
        res_g = QGroupBox("Байкоо")
        res_l = QVBoxLayout()
        self.in_angle = QLineEdit()
        self.in_angle.setPlaceholderText("Компастын бурчу (°)")
        
        btn_check = QPushButton("Жазуу / Текшерүү")
        btn_check.clicked.connect(self.check_val)
        
        res_l.addWidget(self.in_angle)
        res_l.addWidget(btn_check)
        res_g.setLayout(res_l)
        right_panel.addWidget(res_g)
        
        right_panel.addStretch(1)

    def update_params(self):
        I = self.slider_I.value() / 100.0
        self.lbl_I.setText(f"{I:.2f} A")
        
        N = self.spin_N.value()
        has_core = self.chk_core.isChecked()
        
        self.magnet.set_params(I, N, has_core)

    def check_val(self):
        try:
            ang = float(self.in_angle.text())
        except:
            QMessageBox.warning(self, "Ката", "Сан жазыңыз!")
            return
            
        real_ang = self.magnet.current_angle
        if abs(ang - real_ang) < 2.0:
            QMessageBox.information(self, "Туура", "✅ Сиз бурчту туура жаздыңыз!")
        else:
            QMessageBox.warning(self, "Ката", f"❌ Туура эмес. Азыркы бурч: {real_ang:.1f}°")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabElectromagnetApp()
    win.show()
    sys.exit(app.exec())