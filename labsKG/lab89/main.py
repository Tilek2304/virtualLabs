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
# ВИЗУАЛИЗАЦИЯ: Электр кыймылдаткыч
# ==========================================
class MotorWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 400)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")
        
        # Параметрлер
        self.I = 0.0        # Ток
        self.N = 50         # Ороолор
        self.is_reversed = False # Полярдуулук
        
        # Анимация
        self.angle = 0.0    # Ротордун бурчу
        self.speed = 0.0    # Айлануу ылдамдыгы
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(20)

    def set_params(self, I, N, is_reversed):
        self.I = I
        self.N = N
        self.is_reversed = is_reversed
        self.update()

    def animate(self):
        # Ылдамдык токко жана ороолорго жараша болот
        # speed ~ I * N
        target_speed = (self.I * self.N) / 500.0
        
        if self.is_reversed:
            target_speed = -target_speed
            
        # Инерция (жай ылдамдануу)
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

        # 1. Статор (Магниттер)
        # N (Түндүк) - Кызыл
        painter.setBrush(QColor(220, 50, 50))
        painter.setPen(Qt.black)
        painter.drawRect(cx - 150, cy - 60, 60, 120)
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(cx - 130, cy + 10, "N")
        
        # S (Түштүк) - Көк
        painter.setBrush(QColor(50, 50, 220))
        painter.setPen(Qt.black)
        painter.drawRect(cx + 90, cy - 60, 60, 120)
        painter.setPen(Qt.white)
        painter.drawText(cx + 110, cy + 10, "S")

        # 2. Ротор (Айлануучу бөлүк)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle)
        
        # Катушканын каркасы
        painter.setBrush(QColor(200, 200, 200))
        painter.setPen(Qt.black)
        painter.drawRect(-60, -30, 120, 60)
        
        # Ороолор (Зым)
        painter.setPen(QPen(QColor(184, 115, 51), 2))
        for i in range(-50, 60, 10):
            painter.drawLine(i, -25, i, 25)
            
        painter.restore()
        
        # 3. Коммутатор жана Щеткалар
        comm_r = 20
        painter.setBrush(QColor(255, 200, 100)) # Жез
        painter.setPen(Qt.black)
        # Эки жарым шакекче
        painter.drawPie(cx - comm_r, cy - comm_r, comm_r*2, comm_r*2, 
                       int((self.angle + 10)*16), 160*16)
        painter.drawPie(cx - comm_r, cy - comm_r, comm_r*2, comm_r*2, 
                       int((self.angle + 190)*16), 160*16)
                       
        # Щеткалар (Көмүр)
        painter.setBrush(QColor(50, 50, 50))
        painter.drawRect(cx - 10, cy - 35, 20, 10) # Үстүнкү
        painter.drawRect(cx - 10, cy + 25, 20, 10) # Астыңкы
        
        # 4. Ток багыты (Стрелка)
        if abs(self.speed) > 0.1:
            arrow_len = 40
            painter.setPen(QPen(Qt.black, 3))
            
            # Айлануу багыты
            if self.speed > 0: # Саат жебеси боюнча
                painter.drawArc(cx - 60, cy - 60, 120, 120, 45*16, 90*16)
                # Жебенин учу
                # (жөнөкөйлөтүлгөн)
                painter.drawText(cx, cy - 70, "↻")
            else: # Саат жебесине каршы
                painter.drawArc(cx - 60, cy - 60, 120, 120, 45*16, 90*16)
                painter.drawText(cx, cy - 70, "↺")

        # Маалымат
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 10))
        speed_rpm = abs(self.speed) * 100
        painter.drawText(10, 20, f"Ылдамдык: {speed_rpm:.0f} айл/мүн")

# ==========================================
# НЕГИЗГИ ТЕРЕЗЕ
# ==========================================
class LabMotorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш №13: Электр кыймылдаткыч")
        self.resize(1000, 600)
        self.setup_ui()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СОЛ ЖАК: Стенд ---
        left_group = QGroupBox("Кыймылдаткыч модели")
        left_layout = QVBoxLayout()
        self.motor = MotorWidget()
        left_layout.addWidget(self.motor)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- ОҢ ЖАК: Башкаруу ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Тапшырма
        task_g = QGroupBox("Тапшырма")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. Токту (I) көбөйтүп, ылдамдыкты байкаңыз."))
        task_l.addWidget(QLabel("2. Ороолорду (N) өзгөртүп көрүңүз."))
        task_l.addWidget(QLabel("3. Полярдуулукту өзгөртүп, айлануу багытын байкаңыз."))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Параметрлер
        ctrl_g = QGroupBox("Башкаруу")
        ctrl_l = QVBoxLayout()
        
        # Ток
        ctrl_l.addWidget(QLabel("Ток күчү (I):"))
        self.slider_I = QSlider(Qt.Horizontal)
        self.slider_I.setRange(0, 500)
        self.slider_I.setValue(0)
        self.slider_I.valueChanged.connect(self.update_params)
        self.lbl_I = QLabel("0.00 А")
        h_I = QHBoxLayout()
        h_I.addWidget(self.slider_I)
        h_I.addWidget(self.lbl_I)
        ctrl_l.addLayout(h_I)
        
        # Ороолор
        ctrl_l.addWidget(QLabel("Ороолордун саны (N):"))
        self.spin_N = QSpinBox()
        self.spin_N.setRange(10, 500)
        self.spin_N.setValue(50)
        self.spin_N.setSingleStep(10)
        self.spin_N.valueChanged.connect(self.update_params)
        ctrl_l.addWidget(self.spin_N)
        
        # Полярдуулук
        self.chk_rev = QCheckBox("Полярдуулукту өзгөртүү (+/-)")
        self.chk_rev.stateChanged.connect(self.update_params)
        ctrl_l.addWidget(self.chk_rev)
        
        ctrl_g.setLayout(ctrl_l)
        right_panel.addWidget(ctrl_g)

        # 3. Байкоо
        obs_g = QGroupBox("Байкоо")
        obs_l = QVBoxLayout()
        self.in_dir = QLineEdit()
        self.in_dir.setPlaceholderText("Багыты (сааттын жебеси боюнча/сааттын жебесине каршы)")
        
        btn_check = QPushButton("Текшерүү")
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
            QMessageBox.warning(self, "Эскертүү", "Кыймылдаткыч токтоп турат! Ток бериңиз.")
            return
            
        is_cw = real_speed > 0 # Clockwise
        
        if ("саат" in txt and is_cw) or ("каршы" in txt and not is_cw):
            QMessageBox.information(self, "Туура", "✅ Багытты туура аныктадыңыз!")
        else:
            correct = "Саат жебеси боюнча" if is_cw else "Саат жебесине каршы"
            QMessageBox.warning(self, "Ката", f"❌ Туура эмес. Азыркы багыт: {correct}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabMotorApp()
    win.show()
    sys.exit(app.exec())