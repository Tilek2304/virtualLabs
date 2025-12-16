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
# ВИЗУАЛИЗАЦИЯ: Лазер + Решетка + Экран
# ==========================================
class DiffractionWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 450)
        self.setStyleSheet("background-color: #222; border: 1px solid #555; border-radius: 8px;")
        
        self.wavelength = 650 
        self.grating_d = 2000 
        self.distance_L = 1.0 
        
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
        wl = self.wavelength
        if 380 <= wl < 440: return QColor(148, 0, 211) 
        if 440 <= wl < 485: return QColor(0, 0, 255)   
        if 485 <= wl < 500: return QColor(0, 255, 255) 
        if 500 <= wl < 565: return QColor(0, 255, 0)   
        if 565 <= wl < 590: return QColor(255, 255, 0) 
        if 590 <= wl < 625: return QColor(255, 127, 0) 
        if 625 <= wl < 750: return QColor(255, 0, 0)   
        return QColor(255, 255, 255)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h - 50 

        # 1. Лазер
        laser_w = 40
        laser_h = 80
        laser_x = cx - laser_w//2
        laser_y = h - 20
        
        painter.setBrush(QColor(50, 50, 50))
        painter.setPen(QPen(Qt.white, 1))
        painter.drawRect(laser_x, h - 100, laser_w, 60)
        painter.drawText(laser_x + 5, h - 70, "LASER")

        # 2. Решетка
        grating_y = h - 150
        painter.setPen(QPen(Qt.white, 2, Qt.DashLine))
        painter.drawLine(cx - 30, grating_y, cx + 30, grating_y)
        painter.drawText(cx + 40, grating_y + 5, f"d={self.grating_d}nm")

        # 3. Экран
        screen_y = 50
        painter.setBrush(QColor(255, 255, 255, 200)) 
        painter.setPen(Qt.NoPen)
        painter.drawRect(50, 20, w - 100, 60)
        
        # Линейка
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(50, 80, w - 50, 80)
        mid_screen = w // 2
        
        px_per_m = (w - 100) * 2 
        
        for i in range(-20, 21, 5): 
            x = mid_screen + i * (px_per_m / 100.0)
            if 50 <= x <= w - 50:
                h_tick = 10 if i % 10 == 0 else 5
                painter.drawLine(int(x), 80, int(x), 80 + h_tick)
                if i % 10 == 0 and i != 0:
                    painter.drawText(int(x) - 10, 100, f"{i}")
        painter.drawText(mid_screen - 5, 100, "0")
        painter.drawText(w - 40, 100, "см")

        # 4. Лучи
        if self.is_on:
            color = self.get_color()
            pen = QPen(color, 2)
            painter.setPen(pen)
            
            painter.drawLine(cx, h - 100, cx, 20)
            
            for k in [-2, -1, 1, 2]:
                sin_phi = (k * self.wavelength) / self.grating_d
                if abs(sin_phi) < 1.0:
                    phi = math.asin(sin_phi)
                    tan_phi = math.tan(phi)
                    x_dist_m = self.distance_L * tan_phi
                    
                    x_px = mid_screen + x_dist_m * px_per_m
                    
                    painter.drawLine(cx, grating_y, int(x_px), screen_y + 30)
                    
                    painter.setBrush(color)
                    painter.setPen(Qt.NoPen)
                    if 50 <= x_px <= w - 50:
                        painter.drawEllipse(QPointF(x_px, screen_y + 30), 5, 5)
                        
                        if k == 1:
                            b_cm = x_dist_m * 100
                            painter.setPen(Qt.white)
                            painter.drawText(int(x_px), screen_y + 10, f"b={b_cm:.1f}см")

# ==========================================
# ГЛАВНОЕ ОКНО
# ==========================================
class LabDiffractionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №21: Длина световой волны")
        self.resize(1000, 650)
        
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СЛЕВА: Стенд ---
        left_group = QGroupBox("Оптический стенд")
        left_layout = QVBoxLayout()
        self.diffraction = DiffractionWidget()
        left_layout.addWidget(self.diffraction)
        
        h_ctrl = QHBoxLayout()
        btn_laser = QPushButton("Вкл/Выкл Лазер")
        btn_laser.clicked.connect(self.diffraction.toggle_laser)
        h_ctrl.addWidget(btn_laser)
        
        left_layout.addLayout(h_ctrl)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- СПРАВА: Управление ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Задание
        task_g = QGroupBox("Задание")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. Включите лазер."))
        task_l.addWidget(QLabel("2. Измерьте расстояние (b) до 1-го максимума."))
        task_l.addWidget(QLabel("3. Формула: λ = (d * b) / (k * L)"))
        task_l.addWidget(QLabel("   (k=1, L=1м)."))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Параметры
        param_g = QGroupBox("Дано")
        param_l = QVBoxLayout()
        self.lbl_d = QLabel("Период решетки d: ... нм")
        self.lbl_L = QLabel("Расстояние до экрана L: 1.0 м")
        
        param_l.addWidget(self.lbl_d)
        param_l.addWidget(self.lbl_L)
        param_g.setLayout(param_l)
        right_panel.addWidget(param_g)

        # 3. Расчет
        calc_g = QGroupBox("Расчет")
        calc_l = QVBoxLayout()
        
        self.in_b = QLineEdit(); self.in_b.setPlaceholderText("Расстояние b (см)")
        self.in_lambda = QLineEdit(); self.in_lambda.setPlaceholderText("Длина волны λ (нм)")
        
        btn_check = QPushButton("Проверить")
        btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_check.clicked.connect(self.check_answer)
        
        btn_new = QPushButton("Новый лазер")
        btn_new.clicked.connect(self.new_experiment)
        
        calc_l.addWidget(QLabel("Измеренное b (см):"))
        calc_l.addWidget(self.in_b)
        calc_l.addWidget(QLabel("Ответ λ (нм):"))
        calc_l.addWidget(self.in_lambda)
        calc_l.addWidget(btn_check)
        calc_l.addWidget(btn_new)
        
        calc_g.setLayout(calc_l)
        right_panel.addWidget(calc_g)
        
        right_panel.addStretch(1)

    def new_experiment(self):
        self.true_lambda = random.randint(400, 700)
        self.diffraction.set_wavelength(self.true_lambda)
        
        self.diffraction.grating_d = random.choice([2000, 2500, 3000])
        
        self.lbl_d.setText(f"Период решетки d: {self.diffraction.grating_d} нм")
        
        self.in_b.clear()
        self.in_lambda.clear()
        
        QMessageBox.information(self, "Новый опыт", "Установлен новый лазер и решетка.")

    def check_answer(self):
        try:
            val = float(self.in_lambda.text())
        except:
            QMessageBox.warning(self, "Ошибка", "Введите число!")
            return
            
        if abs(val - self.true_lambda) < 10: 
            QMessageBox.information(self, "Верно", f"✅ Отлично! λ = {self.true_lambda} нм")
        else:
            QMessageBox.warning(self, "Ошибка", f"❌ Неверно. λ = {self.true_lambda} нм.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabDiffractionApp()
    win.show()
    sys.exit(app.exec())