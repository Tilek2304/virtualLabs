import sys
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QRadialGradient
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Калориметр + Цилиндр
# ==========================================
class CalorimeterWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 500)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")
        
        self.m1 = 100 
        self.t1 = 20  
        self.m2 = 100 
        self.t2 = 90  
        self.c1 = 4.2 
        self.c2 = 0.9 
        
        self.final_temp = 0
        self.current_temp = 20
        
        self.is_submerged = False
        self.cyl_y = 50 
        self.water_level = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def set_params(self, m1, t1, m2, t2, c2_real):
        self.m1 = m1
        self.t1 = t1
        self.m2 = m2
        self.t2 = t2
        self.c2 = c2_real
        
        self.is_submerged = False
        self.current_temp = t1
        self.cyl_y = 50
        self.update()

    def submerge(self):
        if self.is_submerged: return
        
        numerator = self.c1 * self.m1 * self.t1 + self.c2 * self.m2 * self.t2
        denominator = self.c1 * self.m1 + self.c2 * self.m2
        self.final_temp = numerator / denominator
        
        self.is_submerged = True

    def animate(self):
        target_y = 50
        if self.is_submerged:
            target_y = 350 
            
            diff_t = self.final_temp - self.current_temp
            if abs(diff_t) > 0.1:
                self.current_temp += diff_t * 0.05
            else:
                self.current_temp = self.final_temp
        
        diff_y = target_y - self.cyl_y
        if abs(diff_y) > 1:
            self.cyl_y += diff_y * 0.1
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx = w // 2
        
        # 1. Калориметр
        cw = 220
        ch = 250
        cy = h - 50 - ch
        
        painter.setBrush(QColor(200, 200, 200))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(cx - cw//2 - 10, cy, cw + 20, ch)
        
        painter.setBrush(QColor(240, 240, 255))
        painter.drawRect(cx - cw//2, cy + 10, cw, ch - 20)
        
        # 2. Вода
        base_water_h = (self.m1 / 500) * (ch - 40)
        if base_water_h < 50: base_water_h = 50
        
        water_rise = 0
        if self.cyl_y > cy + ch - base_water_h: 
            water_rise = (self.m2 / 500) * 20 
            
        current_water_h = base_water_h + water_rise
        if current_water_h > ch - 20: current_water_h = ch - 20
        
        temp_ratio = (self.current_temp - 20) / 80 
        if temp_ratio > 1: temp_ratio = 1
        if temp_ratio < 0: temp_ratio = 0
        
        r = int(100 + 155 * temp_ratio)
        b = int(255 - 155 * temp_ratio)
        water_color = QColor(r, 100, b, 180)
        
        water_y = cy + ch - 10 - current_water_h
        
        painter.setBrush(water_color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(cx - cw//2, water_y, cw, current_water_h)
        
        painter.setPen(QPen(water_color.darker(), 2))
        painter.drawLine(cx - cw//2, water_y, cx + cw//2, water_y)

        # 3. Цилиндр
        cyl_w = 40
        cyl_h = 60
        cyl_x = cx - cyl_w//2
        
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(cx, 0, cx, int(self.cyl_y))
        
        cyl_temp_ratio = 0
        if self.is_submerged:
            cyl_temp_ratio = temp_ratio
        else:
            cyl_temp_ratio = (self.t2 - 20) / 80
            
        cr = int(100 + 155 * cyl_temp_ratio)
        cb = int(100 - 100 * cyl_temp_ratio)
        cyl_color = QColor(cr, 50, cb)
        
        painter.setBrush(cyl_color)
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(int(cyl_x), int(self.cyl_y), cyl_w, cyl_h)
        
        # 4. Термометр
        th_x = cx + 80
        th_y = cy - 40
        th_h = 280
        th_w = 12
        
        painter.setBrush(QColor(255, 255, 255))
        painter.drawRect(th_x, th_y, th_w, th_h)
        painter.drawEllipse(th_x - 4, th_y + th_h - 8, 20, 20)
        
        merc_h = (self.current_temp / 100) * (th_h - 20)
        painter.setBrush(QColor(200, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.drawRect(th_x + 3, th_y + th_h - 10 - merc_h, 6, merc_h + 10)
        painter.drawEllipse(th_x - 4, th_y + th_h - 8, 20, 20)
        
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(th_x + 25, th_y + th_h - merc_h, f"{self.current_temp:.1f}°C")

# ==========================================
# ГЛАВНОЕ ОКНО
# ==========================================
class LabSpecificHeatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №11: Удельная теплоемкость")
        self.resize(1000, 650)
        
        self.materials = {
            "Алюминий": 0.92,
            "Медь": 0.38,
            "Железо": 0.46,
            "Латунь": 0.38
        }
        self.current_c2 = 0
        
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СЛЕВА: Калориметр ---
        left_group = QGroupBox("Эксперимент")
        left_layout = QVBoxLayout()
        self.calorimeter = CalorimeterWidget()
        left_layout.addWidget(self.calorimeter)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- СПРАВА: Управление ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Задание
        task_g = QGroupBox("Задание")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. Запишите начальные параметры."))
        task_l.addWidget(QLabel("2. Опустите цилиндр и измерьте конечную температуру (T)."))
        task_l.addWidget(QLabel("3. Рассчитайте теплоемкость цилиндра (c2)."))
        task_l.addWidget(QLabel("Формула: c2 = (c1*m1*(T-t1)) / (m2*(t2-T))"))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Параметры
        param_g = QGroupBox("Дано")
        param_l = QVBoxLayout()
        self.lbl_water = QLabel("Вода (c1=4.2): m1=... г, t1=... °C")
        self.lbl_cyl = QLabel("Цилиндр: m2=... г, t2=... °C")
        
        param_l.addWidget(self.lbl_water)
        param_l.addWidget(self.lbl_cyl)
        param_g.setLayout(param_l)
        right_panel.addWidget(param_g)

        # 3. Действие
        act_g = QGroupBox("Действие")
        act_l = QVBoxLayout()
        btn_submerge = QPushButton("Опустить цилиндр")
        btn_submerge.setStyleSheet("background-color: #FFA726; color: white; font-weight: bold;")
        btn_submerge.clicked.connect(self.calorimeter.submerge)
        act_l.addWidget(btn_submerge)
        act_g.setLayout(act_l)
        right_panel.addWidget(act_g)

        # 4. Ответ
        ans_g = QGroupBox("Ответ")
        ans_l = QVBoxLayout()
        self.in_c2 = QLineEdit()
        self.in_c2.setPlaceholderText("c2 (Дж/г°C)")
        
        btn_check = QPushButton("Проверить")
        btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_check.clicked.connect(self.check_answer)
        
        btn_new = QPushButton("Новый эксперимент")
        btn_new.clicked.connect(self.new_experiment)
        
        ans_l.addWidget(self.in_c2)
        ans_l.addWidget(btn_check)
        ans_l.addWidget(btn_new)
        ans_g.setLayout(ans_l)
        right_panel.addWidget(ans_g)
        
        right_panel.addStretch(1)

    def new_experiment(self):
        self.m1 = random.randint(100, 200) 
        self.t1 = random.randint(15, 25)
        
        self.m2 = random.randint(50, 150) 
        self.t2 = random.randint(80, 95)
        
        name, c2 = random.choice(list(self.materials.items()))
        self.current_c2 = c2
        self.current_material = name
        
        self.lbl_water.setText(f"Вода (c1=4.2): m1={self.m1} г, t1={self.t1} °C")
        self.lbl_cyl.setText(f"Цилиндр: m2={self.m2} г, t2={self.t2} °C")
        
        self.calorimeter.set_params(self.m1, self.t1, self.m2, self.t2, c2)
        self.in_c2.clear()

    def check_answer(self):
        if not self.calorimeter.is_submerged:
            QMessageBox.warning(self, "Ошибка", "Сначала опустите цилиндр!")
            return
            
        try:
            u_c2 = float(self.in_c2.text())
        except:
            QMessageBox.warning(self, "Ошибка", "Введите число!")
            return
            
        if abs(u_c2 - self.current_c2) < 0.1:
            QMessageBox.information(self, "Результат", f"✅ ВЕРНО! Это {self.current_material} (c2={self.current_c2})")
        else:
            QMessageBox.warning(self, "Результат", f"❌ ОШИБКА. Правильно: {self.current_c2}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabSpecificHeatApp()
    win.show()
    sys.exit(app.exec())