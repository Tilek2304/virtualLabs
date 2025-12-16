import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSlider
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QRadialGradient, QPolygonF
from PySide6.QtCore import Qt, QTimer, QPointF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Лазер + Торчо + Экран
# ==========================================
class DiffractionWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 450)
        self.setStyleSheet("background-color: #222; border: 1px solid #555; border-radius: 8px;")
        
        # Параметрлер
        self.wavelength = 650 # нм (Кызыл лазер)
        self.grating_d = 2000 # нм (Торчонун периоду d)
        self.distance_L = 1.0 # метр (Экранга чейин)
        
        self.is_on = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def set_wavelength(self, nm):
        self.wavelength = nm
        self.update()

    def toggle_laser(self):
        self.is_on = not self.is_on
        self.update()

    def get_color(self):
        # Толкун узундугуна жараша түс
        wl = self.wavelength
        if 380 <= wl < 440: return QColor(148, 0, 211) # Violet
        if 440 <= wl < 485: return QColor(0, 0, 255)   # Blue
        if 485 <= wl < 500: return QColor(0, 255, 255) # Cyan
        if 500 <= wl < 565: return QColor(0, 255, 0)   # Green
        if 565 <= wl < 590: return QColor(255, 255, 0) # Yellow
        if 590 <= wl < 625: return QColor(255, 127, 0) # Orange
        if 625 <= wl < 750: return QColor(255, 0, 0)   # Red
        return QColor(255, 255, 255)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h - 50 # Лазер жана торчо астыда

        # 1. Лазер (Түзмөк)
        laser_w = 40
        laser_h = 80
        laser_x = cx - laser_w//2
        laser_y = h - 20
        
        painter.setBrush(QColor(50, 50, 50))
        painter.setPen(QPen(Qt.white, 1))
        painter.drawRect(laser_x, h - 100, laser_w, 60)
        painter.drawText(laser_x + 5, h - 70, "LASER")

        # 2. Торчо (Дифракциялык)
        grating_y = h - 150
        painter.setPen(QPen(Qt.white, 2, Qt.DashLine))
        painter.drawLine(cx - 30, grating_y, cx + 30, grating_y)
        painter.drawText(cx + 40, grating_y + 5, f"d={self.grating_d}нм")

        # 3. Экран (Үстүдө)
        screen_y = 50
        painter.setBrush(QColor(255, 255, 255, 200)) # Жарым тунук ак экран
        painter.setPen(Qt.NoPen)
        painter.drawRect(50, 20, w - 100, 60)
        
        # Сызгыч (Линейка)
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(50, 80, w - 50, 80)
        mid_screen = w // 2
        
        # Пикселдик масштаб (Экрандын туурасы болжол менен 0.5 метр деп алалы)
        # 1 метр = 2 * (w - 100) пиксел
        px_per_m = (w - 100) * 2 
        
        for i in range(-20, 21, 5): # См
            x = mid_screen + i * (px_per_m / 100.0)
            if 50 <= x <= w - 50:
                h_tick = 10 if i % 10 == 0 else 5
                painter.drawLine(int(x), 80, int(x), 80 + h_tick)
                if i % 10 == 0 and i != 0:
                    painter.drawText(int(x) - 10, 100, f"{i}")
        painter.drawText(mid_screen - 5, 100, "0")
        painter.drawText(w - 40, 100, "см")

        # 4. Нурлар (Эгер лазер күйүк болсо)
        if self.is_on:
            color = self.get_color()
            pen = QPen(color, 2)
            painter.setPen(pen)
            
            # Негизги нур (k=0)
            painter.drawLine(cx, h - 100, cx, 20)
            
            # Максимумдар (k=1, k=-1, k=2...)
            # sin(phi) = k * lambda / d
            # x = L * tan(phi)
            
            for k in [-2, -1, 1, 2]:
                sin_phi = (k * self.wavelength) / self.grating_d
                if abs(sin_phi) < 1.0:
                    phi = math.asin(sin_phi)
                    tan_phi = math.tan(phi)
                    x_dist_m = self.distance_L * tan_phi
                    
                    x_px = mid_screen + x_dist_m * px_per_m
                    
                    # Нурду тартуу
                    painter.drawLine(cx, grating_y, int(x_px), screen_y + 30)
                    
                    # Экрандагы так (spot)
                    painter.setBrush(color)
                    painter.setPen(Qt.NoPen)
                    if 50 <= x_px <= w - 50:
                        painter.drawEllipse(QPointF(x_px, screen_y + 30), 5, 5)
                        
                        # Аралыкты жазуу (b)
                        if k == 1:
                            b_cm = x_dist_m * 100
                            painter.setPen(Qt.white)
                            painter.drawText(int(x_px), screen_y + 10, f"b={b_cm:.1f}см")

# ==========================================
# НЕГИЗГИ ТЕРЕЗЕ
# ==========================================
class LabDiffractionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш №21: Жарык толкунунун узундугу")
        self.resize(1000, 650)
        
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СОЛ ЖАК: Стенд ---
        left_group = QGroupBox("Оптикалык стенд")
        left_layout = QVBoxLayout()
        self.diffraction = DiffractionWidget()
        left_layout.addWidget(self.diffraction)
        
        # Лазерди башкаруу
        h_ctrl = QHBoxLayout()
        btn_laser = QPushButton("Лазерди Күйгүзүү/Өчүрүү")
        btn_laser.clicked.connect(self.diffraction.toggle_laser)
        h_ctrl.addWidget(btn_laser)
        
        left_layout.addLayout(h_ctrl)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- ОҢ ЖАК: Башкаруу ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Тапшырма
        task_g = QGroupBox("Тапшырма")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. Лазерди күйгүзүңүз."))
        task_l.addWidget(QLabel("2. Экрандан борбордук жана 1-тартиптеги максимумдун аралыгын (b) көрүңүз."))
        task_l.addWidget(QLabel("3. Формула: λ = (d * b) / (k * L)"))
        task_l.addWidget(QLabel("   (k=1, L=1м деп алыңыз)."))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Параметрлер
        param_g = QGroupBox("Берилгендер")
        param_l = QVBoxLayout()
        self.lbl_d = QLabel("Торчо туруктуусу d: ... нм")
        self.lbl_L = QLabel("Экранга чейин L: 1.0 м")
        
        param_l.addWidget(self.lbl_d)
        param_l.addWidget(self.lbl_L)
        param_g.setLayout(param_l)
        right_panel.addWidget(param_g)

        # 3. Эсептөө
        calc_g = QGroupBox("Эсептөө")
        calc_l = QVBoxLayout()
        
        self.in_b = QLineEdit(); self.in_b.setPlaceholderText("Аралык b (см)")
        self.in_lambda = QLineEdit(); self.in_lambda.setPlaceholderText("Толкун узундугу λ (нм)")
        
        btn_check = QPushButton("Текшерүү")
        btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_check.clicked.connect(self.check_answer)
        
        btn_new = QPushButton("Жаңы лазер")
        btn_new.clicked.connect(self.new_experiment)
        
        calc_l.addWidget(QLabel("Өлчөнгөн b (см):"))
        calc_l.addWidget(self.in_b)
        calc_l.addWidget(QLabel("Жооп λ (нм):"))
        calc_l.addWidget(self.in_lambda)
        calc_l.addWidget(btn_check)
        calc_l.addWidget(btn_new)
        
        calc_g.setLayout(calc_l)
        right_panel.addWidget(calc_g)
        
        right_panel.addStretch(1)

    def new_experiment(self):
        # Жаңы толкун узундугу (400 - 700 нм)
        self.true_lambda = random.randint(400, 700)
        self.diffraction.set_wavelength(self.true_lambda)
        
        # Торчону да өзгөртсө болот (мисалы 2000, 2500, 3000 нм)
        self.diffraction.grating_d = random.choice([2000, 2500, 3000])
        
        self.lbl_d.setText(f"Торчо туруктуусу d: {self.diffraction.grating_d} нм")
        
        self.in_b.clear()
        self.in_lambda.clear()
        
        QMessageBox.information(self, "Жаңы", "Жаңы лазер жана торчо коюлду.")

    def check_answer(self):
        try:
            val = float(self.in_lambda.text())
        except:
            QMessageBox.warning(self, "Ката", "Сан жазыңыз!")
            return
            
        if abs(val - self.true_lambda) < 10: # +/- 10 нм каталык
            QMessageBox.information(self, "Туура", f"✅ Азаматсыз! λ = {self.true_lambda} нм")
        else:
            QMessageBox.warning(self, "Ката", f"❌ Туура эмес. λ = {self.true_lambda} нм болушу керек.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabDiffractionApp()
    win.show()
    sys.exit(app.exec())