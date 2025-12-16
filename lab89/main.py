import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox, QGroupBox, QSpinBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QRadialGradient, QLinearGradient
from PySide6.QtCore import Qt, QTimer, QPointF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Электродвигатель
# ==========================================
class MotorWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 400)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")
        
        self.I = 0.0        
        self.N = 50         
        self.is_reversed = False 
        
        self.angle = 0.0    
        self.speed = 0.0    
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(20)

    def set_params(self, I, N, is_reversed):
        self.I = I
        self.N = N
        self.is_reversed = is_reversed
        self.update()

    def animate(self):
        target_speed = (self.I * self.N) / 500.0
        
        if self.is_reversed:
            target_speed = -target_speed
            
        diff = target_speed - self.speed
        self.speed += diff * 0.05
        
        self.angle += self.speed
        if self.angle > 360: self.angle -= 360
        if self.angle < 0: self.angle += 360
        
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        # 1. Статор
        painter.setBrush(QColor(220, 50, 50))
        painter.setPen(Qt.black)
        painter.drawRect(cx - 150, cy - 60, 60, 120)
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(cx - 130, cy + 10, "N")
        
        painter.setBrush(QColor(50, 50, 220))
        painter.setPen(Qt.black)
        painter.drawRect(cx + 90, cy - 60, 60, 120)
        painter.setPen(Qt.white)
        painter.drawText(cx + 110, cy + 10, "S")

        # 2. Ротор
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle)
        
        painter.setBrush(QColor(200, 200, 200))
        painter.setPen(Qt.black)
        painter.drawRect(-60, -30, 120, 60)
        
        painter.setPen(QPen(QColor(184, 115, 51), 2))
        for i in range(-50, 60, 10):
            painter.drawLine(i, -25, i, 25)
            
        painter.restore()
        
        # 3. Коммутатор
        comm_r = 20
        painter.setBrush(QColor(255, 200, 100)) 
        painter.setPen(Qt.black)
        painter.drawPie(cx - comm_r, cy - comm_r, comm_r*2, comm_r*2, 
                       int((self.angle + 10)*16), 160*16)
        painter.drawPie(cx - comm_r, cy - comm_r, comm_r*2, comm_r*2, 
                       int((self.angle + 190)*16), 160*16)
                       
        painter.setBrush(QColor(50, 50, 50))
        painter.drawRect(cx - 10, cy - 35, 20, 10) 
        painter.drawRect(cx - 10, cy + 25, 20, 10) 
        
        # 4. Стрелка
        if abs(self.speed) > 0.1:
            painter.setPen(QPen(Qt.black, 3))
            if self.speed > 0: 
                painter.drawArc(cx - 60, cy - 60, 120, 120, 45*16, 90*16)
                painter.drawText(cx, cy - 70, "↻")
            else: 
                painter.drawArc(cx - 60, cy - 60, 120, 120, 45*16, 90*16)
                painter.drawText(cx, cy - 70, "↺")

        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 10))
        speed_rpm = abs(self.speed) * 100
        painter.drawText(10, 20, f"Скорость: {speed_rpm:.0f} об/мин")

# ==========================================
# ГЛАВНОЕ ОКНО
# ==========================================
class LabMotorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №13: Электродвигатель")
        self.resize(1000, 600)
        self.setup_ui()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СЛЕВА: Стенд ---
        left_group = QGroupBox("Модель двигателя")
        left_layout = QVBoxLayout()
        self.motor = MotorWidget()
        left_layout.addWidget(self.motor)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- СПРАВА: Управление ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Задание
        task_g = QGroupBox("Задание")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. Изменяйте ток (I) и наблюдайте за скоростью."))
        task_l.addWidget(QLabel("2. Изменяйте число витков (N)."))
        task_l.addWidget(QLabel("3. Измените полярность и направление вращения."))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Параметры
        ctrl_g = QGroupBox("Управление")
        ctrl_l = QVBoxLayout()
        
        ctrl_l.addWidget(QLabel("Сила тока (I):"))
        self.slider_I = QSlider(Qt.Horizontal)
        self.slider_I.setRange(0, 500)
        self.slider_I.setValue(0)
        self.slider_I.valueChanged.connect(self.update_params)
        self.lbl_I = QLabel("0.00 А")
        h_I = QHBoxLayout()
        h_I.addWidget(self.slider_I)
        h_I.addWidget(self.lbl_I)
        ctrl_l.addLayout(h_I)
        
        ctrl_l.addWidget(QLabel("Число витков (N):"))
        self.spin_N = QSpinBox()
        self.spin_N.setRange(10, 500)
        self.spin_N.setValue(50)
        self.spin_N.setSingleStep(10)
        self.spin_N.valueChanged.connect(self.update_params)
        ctrl_l.addWidget(self.spin_N)
        
        self.chk_rev = QCheckBox("Обратная полярность (+/-)")
        self.chk_rev.stateChanged.connect(self.update_params)
        ctrl_l.addWidget(self.chk_rev)
        
        ctrl_g.setLayout(ctrl_l)
        right_panel.addWidget(ctrl_g)

        # 3. Наблюдение
        obs_g = QGroupBox("Наблюдение")
        obs_l = QVBoxLayout()
        self.in_dir = QLineEdit()
        self.in_dir.setPlaceholderText("Направление (По часовой / Против)")
        
        btn_check = QPushButton("Проверить")
        btn_check.clicked.connect(self.check_val)
        
        obs_l.addWidget(self.in_dir)
        obs_l.addWidget(btn_check)
        obs_g.setLayout(obs_l)
        right_panel.addWidget(obs_g)
        
        right_panel.addStretch(1)

    def update_params(self):
        I = self.slider_I.value() / 100.0
        self.lbl_I.setText(f"{I:.2f} A")
        
        N = self.spin_N.value()
        is_rev = self.chk_rev.isChecked()
        
        self.motor.set_params(I, N, is_rev)

    def check_val(self):
        txt = self.in_dir.text().lower()
        real_speed = self.motor.speed
        
        if abs(real_speed) < 0.1:
            QMessageBox.warning(self, "Внимание", "Двигатель стоит! Подайте ток.")
            return
            
        is_cw = real_speed > 0 
        
        if ("по" in txt and is_cw) or ("против" in txt and not is_cw):
            QMessageBox.information(self, "Верно", "✅ Направление определено верно!")
        else:
            correct = "По часовой" if is_cw else "Против часовой"
            QMessageBox.warning(self, "Ошибка", f"❌ Неверно. Текущее направление: {correct}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabMotorApp()
    win.show()
    sys.exit(app.exec())