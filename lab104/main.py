import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QRadialGradient, QLinearGradient
from PySide6.QtCore import Qt, QTimer, QPointF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Калориметр + Омметр
# ==========================================
class ResistanceWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 400)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")
        
        self.R0 = 10.0  
        self.T0 = 20.0  
        self.alpha = 0.004 
        
        self.current_T = 20.0
        self.target_T = 20.0
        
        self.needle_angle = -45.0 
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def set_params(self, R0, alpha):
        self.R0 = R0
        self.alpha = alpha
        self.current_T = 20.0
        self.target_T = 20.0
        self.update()

    def heat_up(self):
        self.target_T = random.uniform(80, 95)

    def get_resistance(self):
        return self.R0 * (1 + self.alpha * (self.current_T - 20))

    def animate(self):
        diff = self.target_T - self.current_T
        if abs(diff) > 0.1:
            self.current_T += diff * 0.02
        else:
            self.current_T = self.target_T
            
        current_R = self.get_resistance()
        min_R = self.R0 * 0.9
        max_R = self.R0 * 1.5
        
        ratio = (current_R - min_R) / (max_R - min_R)
        target_angle = -45 + ratio * 90
        
        self.needle_angle += (target_angle - self.needle_angle) * 0.1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        # 1. Калориметр
        cal_x = cx - 150
        cal_y = cy
        cal_w = 140
        cal_h = 180
        
        temp_ratio = (self.current_T - 20) / 80
        if temp_ratio > 1: temp_ratio = 1
        r = int(100 + 155 * temp_ratio)
        b = int(255 - 155 * temp_ratio)
        
        painter.setBrush(QColor(r, 100, b, 180))
        painter.setPen(Qt.black)
        painter.drawRect(cal_x, cal_y, cal_w, cal_h)
        
        painter.setPen(QPen(QColor(184, 115, 51), 3))
        for i in range(5):
            y = cal_y + 30 + i * 25
            painter.drawArc(cal_x + 20, y, cal_w - 40, 40, 0, 180*16)
            painter.drawArc(cal_x + 20, y + 20, cal_w - 40, 40, 180*16, 180*16)

        # 2. Термометр
        th_x = cal_x + 20
        th_y = cal_y - 60
        th_h = 220
        
        painter.setBrush(Qt.white)
        painter.setPen(Qt.black)
        painter.drawRect(th_x, th_y, 15, th_h)
        painter.drawEllipse(th_x - 5, th_y + th_h - 10, 25, 25)
        
        merc_h = (self.current_T / 100) * (th_h - 20)
        painter.setBrush(Qt.red)
        painter.setPen(Qt.NoPen)
        painter.drawRect(th_x + 2, th_y + th_h - 10 - merc_h, 11, merc_h + 10)
        painter.drawEllipse(th_x - 5, th_y + th_h - 10, 25, 25)
        
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(th_x + 25, th_y + th_h - merc_h, f"{self.current_T:.1f}°C")

        # 3. Омметр
        om_x = cx + 100
        om_y = cy + 50
        om_r = 70
        
        painter.setBrush(QColor(240, 240, 240))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawEllipse(QPointF(om_x, om_y), om_r, om_r)
        
        painter.drawText(om_x - 10, om_y + 40, "Ω")
        
        painter.save()
        painter.translate(om_x, om_y)
        painter.rotate(self.needle_angle)
        painter.setPen(QPen(Qt.red, 3))
        painter.drawLine(0, 0, 0, -om_r + 10)
        painter.setBrush(Qt.black)
        painter.drawEllipse(QPointF(0,0), 5, 5)
        painter.restore()
        
        current_R = self.get_resistance()
        painter.drawText(om_x - 30, om_y + 90, f"R = {current_R:.2f} Ом")
        
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(cal_x + cal_w, cal_y + 50, om_x - om_r, om_y)

# ==========================================
# ГЛАВНОЕ ОКНО
# ==========================================
class LabTempCoeffApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №15: Температурный коэффициент")
        self.resize(1000, 600)
        
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СЛЕВА: Стенд ---
        left_group = QGroupBox("Стенд")
        left_layout = QVBoxLayout()
        self.res_widget = ResistanceWidget()
        left_layout.addWidget(self.res_widget)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- СПРАВА: Управление ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Задание
        task_g = QGroupBox("Задание")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. Запишите начальные T0 и R0."))
        task_l.addWidget(QLabel("2. Нажмите 'Нагреть'."))
        task_l.addWidget(QLabel("3. Запишите конечные T и R."))
        task_l.addWidget(QLabel("4. Вычислите α = (R - R0) / (R0 * (T - T0))."))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Управление
        ctrl_g = QGroupBox("Управление")
        ctrl_l = QVBoxLayout()
        
        btn_heat = QPushButton("Нагреть")
        btn_heat.setStyleSheet("background-color: #FF5722; color: white; font-weight: bold;")
        btn_heat.clicked.connect(self.res_widget.heat_up)
        
        ctrl_l.addWidget(btn_heat)
        ctrl_g.setLayout(ctrl_l)
        right_panel.addWidget(ctrl_g)

        # 3. Вычисление
        calc_g = QGroupBox("Вычисление")
        calc_l = QVBoxLayout()
        
        self.in_R0 = QLineEdit(); self.in_R0.setPlaceholderText("R0 (Ом)")
        self.in_T0 = QLineEdit("20"); self.in_T0.setPlaceholderText("T0 (°C)")
        self.in_R = QLineEdit(); self.in_R.setPlaceholderText("R (Ом)")
        self.in_T = QLineEdit(); self.in_T.setPlaceholderText("T (°C)")
        self.in_alpha = QLineEdit(); self.in_alpha.setPlaceholderText("α (1/°C)")
        
        calc_l.addWidget(QLabel("Начальные данные:"))
        calc_l.addWidget(self.in_R0)
        calc_l.addWidget(self.in_T0)
        calc_l.addWidget(QLabel("Конечные данные:"))
        calc_l.addWidget(self.in_R)
        calc_l.addWidget(self.in_T)
        calc_l.addWidget(QLabel("Коэффициент α:"))
        calc_l.addWidget(self.in_alpha)
        
        btn_check = QPushButton("Проверить")
        btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_check.clicked.connect(self.check_answer)
        
        btn_new = QPushButton("Новый эксперимент")
        btn_new.clicked.connect(self.new_experiment)
        
        calc_l.addWidget(btn_check)
        calc_l.addWidget(btn_new)
        
        calc_g.setLayout(calc_l)
        right_panel.addWidget(calc_g)
        
        right_panel.addStretch(1)

    def new_experiment(self):
        materials = [
            ("Медь", 0.0043),
            ("Алюминий", 0.0042),
            ("Железо", 0.006),
            ("Вольфрам", 0.0045)
        ]
        name, alpha = random.choice(materials)
        self.true_alpha = alpha
        
        R0 = random.uniform(5.0, 20.0)
        self.res_widget.set_params(R0, alpha)
        
        self.in_R0.clear()
        self.in_R.clear()
        self.in_T.clear()
        self.in_alpha.clear()
        
        QMessageBox.information(self, "Задание", f"Дана новая проволока ({name}).")

    def check_answer(self):
        try:
            val = float(self.in_alpha.text())
        except:
            QMessageBox.warning(self, "Ошибка", "Введите число!")
            return
            
        if abs(val - self.true_alpha) < 0.0005:
            QMessageBox.information(self, "Верно", f"✅ Отлично! α = {self.true_alpha}")
        else:
            QMessageBox.warning(self, "Ошибка", f"❌ Неверно. α = {self.true_alpha}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabTempCoeffApp()
    win.show()
    sys.exit(app.exec())