import sys
import math
import random
from statistics import mean
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSlider
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QRadialGradient
from PySide6.QtCore import Qt, QTimer, QPointF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Пружина
# ==========================================
class SpringWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 550)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")

        # Физические параметры
        self.px_per_cm = 15.0   # 1 см = 15 пикселей
        self.natural_len_cm = 10.0
        self.k = 50.0           # Н/м (скрыто)
        self.mass = 0.0         # кг
        self.g = 9.81

        # Анимация
        self.current_y = 0.0
        self.target_y = 0.0
        self.velocity = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(20)

        self.reset_spring()

    def reset_spring(self):
        natural_px = self.natural_len_cm * self.px_per_cm
        self.current_y = natural_px
        self.target_y = natural_px
        self.velocity = 0.0

    def set_experiment(self, k_val):
        self.k = k_val
        self.update_physics()

    def set_mass(self, mass_g):
        self.mass = mass_g / 1000.0 # грамм -> кг
        self.update_physics()

    def update_physics(self):
        # F = k * x  =>  m*g = k * x  =>  x = (m*g)/k
        if self.k <= 0: return
        
        extension_m = (self.mass * self.g) / self.k
        extension_cm = extension_m * 100.0
        extension_px = extension_cm * self.px_per_cm
        
        natural_px = self.natural_len_cm * self.px_per_cm
        self.target_y = natural_px + extension_px

    def animate(self):
        force = (self.target_y - self.current_y) * 0.1
        self.velocity += force
        self.velocity *= 0.85 # Затухание
        self.current_y += self.velocity
        
        if abs(self.velocity) < 0.01 and abs(self.target_y - self.current_y) < 0.1:
            self.current_y = self.target_y
            self.velocity = 0
            
        self.update()

    def get_extension_cm(self):
        natural_px = self.natural_len_cm * self.px_per_cm
        diff_px = self.current_y - natural_px
        return diff_px / self.px_per_cm

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx = w // 2
        top_y = 40

        # 1. Линейка
        ruler_x = 40
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Arial", 8))
        
        zero_y = top_y + self.natural_len_cm * self.px_per_cm
        
        for i in range(21): # 0..20 см
            y = zero_y + i * self.px_per_cm
            if y > h - 10: break
            
            painter.drawLine(ruler_x, int(y), ruler_x + 15, int(y))
            painter.drawText(ruler_x - 30, int(y) + 5, f"{i}")
            
            for j in range(1, 5):
                sub_y = y + j * (self.px_per_cm / 5)
                painter.drawLine(ruler_x, int(sub_y), ruler_x + 8, int(sub_y))

        painter.drawText(ruler_x - 35, int(zero_y) - 15, "см")

        # 2. Пружина
        painter.setPen(QPen(QColor(80, 80, 80), 3))
        painter.drawLine(cx - 20, top_y, cx + 20, top_y)
        
        coils = 15
        spring_h = self.current_y
        step = spring_h / coils
        
        path = list()
        path.append(QPointF(cx, top_y))
        
        for i in range(coils):
            y_curr = top_y + i * step
            offset = 15 if i % 2 == 0 else -15
            path.append(QPointF(cx + offset, y_curr + step/2))
        
        path.append(QPointF(cx, top_y + spring_h))
        
        for i in range(len(path) - 1):
            painter.drawLine(path[i], path[i+1])

        # 3. Груз
        if self.mass > 0:
            bottom_y = top_y + spring_h
            box_w = 50
            box_h = 50 + (self.mass * 10)
            if box_h > 100: box_h = 100
            
            painter.setPen(QPen(Qt.black, 2))
            painter.drawLine(cx, int(bottom_y), cx, int(bottom_y + 15))
            
            grad = QLinearGradient(cx - box_w/2, 0, cx + box_w/2, 0)
            grad.setColorAt(0, QColor(100, 100, 100))
            grad.setColorAt(0.5, QColor(200, 200, 200))
            grad.setColorAt(1, QColor(80, 80, 80))
            
            painter.setBrush(grad)
            painter.drawRect(int(cx - box_w/2), int(bottom_y + 15), int(box_w), int(box_h))
            
            painter.setPen(Qt.black)
            painter.setFont(QFont("Arial", 10, QFont.Bold))
            mass_g = int(self.mass * 1000)
            painter.drawText(int(cx - box_w/2), int(bottom_y + 15), int(box_w), int(box_h), Qt.AlignCenter, f"{mass_g} г")
            
            # Стрелка
            painter.setPen(QPen(Qt.red, 2))
            arrow_y = bottom_y
            painter.drawLine(cx, int(arrow_y), ruler_x + 20, int(arrow_y))
            painter.drawText(ruler_x + 25, int(arrow_y) + 5, "◄")


# ==========================================
# ГЛАВНОЕ ОКНО
# ==========================================
class LabSpringApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №6: Закон Гука")
        self.resize(1100, 700)
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СЛЕВА: Стенд ---
        left_group = QGroupBox("Стенд")
        left_layout = QVBoxLayout()
        self.spring = SpringWidget()
        left_layout.addWidget(self.spring)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 1)

        # --- СПРАВА: Управление ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Задание
        task_g = QGroupBox("Задание")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. Меняйте массу груза ползунком."))
        task_l.addWidget(QLabel("2. Измерьте удлинение (x) по линейке."))
        task_l.addWidget(QLabel("3. Формула: F = k * x  (F = m * g)."))
        task_l.addWidget(QLabel("4. Вычислите жесткость: k = (m * g) / x."))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Управление массой
        ctrl_g = QGroupBox("Масса груза")
        ctrl_l = QVBoxLayout()
        
        self.lbl_mass = QLabel("Масса: 0 г")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 500)
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(50)
        self.slider.valueChanged.connect(self.update_mass)
        
        ctrl_l.addWidget(self.lbl_mass)
        ctrl_l.addWidget(self.slider)
        ctrl_g.setLayout(ctrl_l)
        right_panel.addWidget(ctrl_g)

        # 3. Ввод данных
        inp_g = QGroupBox("Вычисления")
        inp_l = QVBoxLayout()
        
        self.in_m = QLineEdit(); self.in_m.setPlaceholderText("Масса m (кг!)")
        self.in_x = QLineEdit(); self.in_x.setPlaceholderText("Удлинение x (м!)")
        self.in_k = QLineEdit(); self.in_k.setPlaceholderText("Жесткость k (Н/м)")
        
        inp_l.addWidget(QLabel("Масса (кг):"))
        inp_l.addWidget(self.in_m)
        inp_l.addWidget(QLabel("Удлинение (метр):"))
        inp_l.addWidget(self.in_x)
        inp_l.addWidget(QLabel("Жесткость (k):"))
        inp_l.addWidget(self.in_k)
        inp_g.setLayout(inp_l)
        right_panel.addWidget(inp_g)

        # 4. Кнопки
        btn_check = QPushButton("Проверить и Добавить")
        btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_check.clicked.connect(self.check_answer)
        
        btn_new = QPushButton("Новая пружина (Новое k)")
        btn_new.clicked.connect(self.new_experiment)
        
        right_panel.addWidget(btn_check)
        right_panel.addWidget(btn_new)

        # 5. Таблица
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["m (кг)", "x (м)", "k (Н/м)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_panel.addWidget(QLabel("Результаты:"))
        right_panel.addWidget(self.table)
        
        self.lbl_res = QLabel("")
        right_panel.addWidget(self.lbl_res)

    def new_experiment(self):
        # Случайное k (20..100)
        self.true_k = random.randint(20, 100)
        self.spring.set_experiment(self.true_k)
        
        self.slider.setValue(0)
        self.in_m.clear()
        self.in_x.clear()
        self.in_k.clear()
        self.table.setRowCount(0)
        self.lbl_res.setText(f"--- Дана новая пружина ---")

    def update_mass(self):
        val = self.slider.value()
        self.lbl_mass.setText(f"Масса: {val} г")
        self.spring.set_mass(val)
        
        self.in_m.setText(str(val / 1000.0))
        
        # Получаем текущее удлинение
        x_cm = self.spring.get_extension_cm()
        self.in_x.setText(f"{x_cm / 100.0:.3f}")

    def check_answer(self):
        try:
            u_k = float(self.in_k.text())
        except:
            QMessageBox.warning(self, "Ошибка", "Введите корректное число!")
            return

        error_margin = self.true_k * 0.05
        if abs(u_k - self.true_k) <= error_margin:
            self.lbl_res.setText(f"<span style='color:green'><b>ВЕРНО! k ≈ {self.true_k} Н/м</b></span>")
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(self.in_m.text()))
            self.table.setItem(row, 1, QTableWidgetItem(self.in_x.text()))
            self.table.setItem(row, 2, QTableWidgetItem(str(u_k)))
        else:
            self.lbl_res.setText(f"<span style='color:red'><b>ОШИБКА. Правильно: {self.true_k} Н/м</b></span>")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabSpringApp()
    win.show()
    sys.exit(app.exec())