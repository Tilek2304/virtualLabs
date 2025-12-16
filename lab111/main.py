import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer, QPointF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Маятник + Секундомер
# ==========================================
class PendulumWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 450)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")
        
        # Внутренние параметры (Скрыты от ученика)
        self.length = 1.0   
        self.g = 9.81       
        
        # Анимация
        self.angle = 0.0    
        self.max_angle = math.radians(15)
        self.time = 0.0     
        self.is_running = False
        
        self.stopwatch_time = 0.0
        self.stopwatch_running = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(20) 

    def set_physics(self, l, g):
        self.length = l
        self.g = g
        self.reset()

    def reset(self):
        self.time = 0.0
        self.angle = self.max_angle
        self.is_running = False
        self.stopwatch_time = 0.0
        self.stopwatch_running = False
        self.update()

    def start_swing(self):
        self.is_running = True

    def toggle_stopwatch(self):
        self.stopwatch_running = not self.stopwatch_running

    def reset_stopwatch(self):
        self.stopwatch_time = 0.0
        self.stopwatch_running = False
        self.update()

    def animate(self):
        if self.is_running:
            self.time += 0.02
            # Частота зависит от g и l
            omega = math.sqrt(self.g / self.length)
            self.angle = self.max_angle * math.cos(omega * self.time)
            
        if self.stopwatch_running:
            self.stopwatch_time += 0.02
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, 50

        # Штатив
        painter.setPen(QPen(Qt.black, 3))
        painter.drawLine(cx - 50, cy, cx + 50, cy)
        
        # Нить
        scale = 250 
        l_px = self.length * scale
        if l_px > h - 100: l_px = h - 100
        
        bx = cx + l_px * math.sin(self.angle)
        by = cy + l_px * math.cos(self.angle)
        
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(cx, cy, bx, by)
        
        painter.setBrush(QColor(200, 50, 50))
        painter.setPen(Qt.black)
        painter.drawEllipse(QPointF(bx, by), 15, 15)

        # Секундомер
        sw_x = w - 130
        sw_y = 80
        painter.setBrush(QColor(40, 40, 40))
        painter.setPen(Qt.black)
        painter.drawRect(sw_x, sw_y, 110, 50)
        
        painter.setPen(QColor(0, 255, 0))
        painter.setFont(QFont("Courier", 22, QFont.Bold))
        painter.drawText(sw_x + 10, sw_y + 35, f"{self.stopwatch_time:.2f}")
        
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 10))
        painter.drawText(sw_x, sw_y - 5, "Секундомер")

# ==========================================
# ГЛАВНОЕ ОКНО
# ==========================================
class LabFrequencyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа: Определение частоты колебаний")
        self.resize(1000, 600)
        
        self.true_freq = 0.0
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СЛЕВА: Стенд ---
        left_group = QGroupBox("Стенд")
        left_layout = QVBoxLayout()
        self.pendulum = PendulumWidget()
        left_layout.addWidget(self.pendulum)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- СПРАВА: Управление ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Задание
        task_g = QGroupBox("Задание")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. Нажмите 'Раскачать'."))
        task_l.addWidget(QLabel("2. Запустите секундомер и отсчитайте ровно 10 колебаний."))
        task_l.addWidget(QLabel("3. Запишите время (t) и вычислите частоту."))
        task_l.addWidget(QLabel("Формула: ν = N / t (Герц)"))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Инструменты
        ctrl_g = QGroupBox("Инструменты")
        ctrl_l = QVBoxLayout()
        
        btn_swing = QPushButton("1. Раскачать")
        btn_swing.clicked.connect(self.pendulum.start_swing)
        
        self.btn_timer = QPushButton("2. Секундомер (Старт/Стоп)")
        self.btn_timer.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.btn_timer.clicked.connect(self.toggle_timer_text)
        
        btn_reset_timer = QPushButton("Сброс секундомера")
        btn_reset_timer.clicked.connect(self.pendulum.reset_stopwatch)
        
        ctrl_l.addWidget(btn_swing)
        ctrl_l.addWidget(self.btn_timer)
        ctrl_l.addWidget(btn_reset_timer)
        ctrl_g.setLayout(ctrl_l)
        right_panel.addWidget(ctrl_g)

        # 3. Расчет
        calc_g = QGroupBox("Ваши расчеты")
        calc_l = QVBoxLayout()
        
        self.in_t = QLineEdit(); self.in_t.setPlaceholderText("Время t (с)")
        self.in_freq = QLineEdit(); self.in_freq.setPlaceholderText("Частота ν (Гц)")
        
        calc_l.addWidget(QLabel("Время 10 колебаний (t):"))
        calc_l.addWidget(self.in_t)
        calc_l.addWidget(QLabel("Частота колебаний (ν = 10/t):"))
        calc_l.addWidget(self.in_freq)
        
        btn_check = QPushButton("Проверить")
        btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_check.clicked.connect(self.check_answer)
        
        btn_new = QPushButton("Новый опыт")
        btn_new.clicked.connect(self.new_experiment)
        
        calc_l.addWidget(btn_check)
        calc_l.addWidget(btn_new)
        
        calc_g.setLayout(calc_l)
        right_panel.addWidget(calc_g)
        
        right_panel.addStretch(1)

    def toggle_timer_text(self):
        self.pendulum.toggle_stopwatch()
        if self.pendulum.stopwatch_running:
            self.btn_timer.setText("СТОП")
            self.btn_timer.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        else:
            self.btn_timer.setText("СТАРТ")
            self.btn_timer.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

    def new_experiment(self):
        # РАНДОМНЫЕ УСЛОВИЯ (g и l)
        l = random.uniform(0.5, 1.5) 
        g = random.uniform(3.0, 20.0) # Разная гравитация
        
        self.pendulum.set_physics(l, g)
        
        # Считаем правильный ответ
        true_T = 2 * math.pi * math.sqrt(l / g)
        self.true_freq = 1.0 / true_T
        
        self.in_t.clear(); self.in_freq.clear()
        self.pendulum.reset_stopwatch()
        self.btn_timer.setText("2. Секундомер (Старт/Стоп)")
        self.btn_timer.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        
        QMessageBox.information(self, "Новый опыт", "Условия изменены (другая планета?).\nИзмерьте частоту колебаний.")

    def check_answer(self):
        try:
            val = float(self.in_freq.text())
        except:
            QMessageBox.warning(self, "Ошибка", "Введите число!")
            return
            
        # Допуск 8% на реакцию человека
        error_percent = abs(val - self.true_freq) / self.true_freq * 100
        
        if error_percent < 8.0:
            QMessageBox.information(self, "Верно", f"✅ Отлично! Ваша частота: {val:.3f} Гц\n(Точная: {self.true_freq:.3f} Гц)")
        else:
            QMessageBox.warning(self, "Ошибка", f"❌ Неверно.\nВы ввели: {val:.3f} Гц\nТочная: {self.true_freq:.3f} Гц\n\nПопробуйте точнее измерить время.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabFrequencyApp()
    win.show()
    sys.exit(app.exec())