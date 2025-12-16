import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
)
# Добавлен QPainterPath
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QLinearGradient, QPainterPath
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Стенд трения
# ==========================================
class FrictionWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 350)
        self.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 8px;")

        # Физика
        self.g = 9.81
        self.block_mass = 0.100 
        self.weight_mass = 0.100 
        self.weights_count = 0
        
        self.mu = 0.3 
        self.surface_color = QColor(222, 184, 135) 
        
        self.current_force = 0.0
        
        # Анимация
        self.block_x = 50
        self.is_pulling = False
        self.spring_len = 0 
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(20)

    def set_surface(self, index):
        if index == 0: 
            self.mu = 0.3
            self.surface_color = QColor(222, 184, 135) # Дерево
        elif index == 1: 
            self.mu = 0.15
            self.surface_color = QColor(200, 230, 255) # Пластик
        elif index == 2: 
            self.mu = 0.6
            self.surface_color = QColor(100, 100, 100) # Наждачка
        self.reset_pos()

    def add_weight(self):
        if self.weights_count < 4:
            self.weights_count += 1
            self.reset_pos()

    def remove_weight(self):
        if self.weights_count > 0:
            self.weights_count -= 1
            self.reset_pos()

    def start_pull(self):
        self.is_pulling = True
        # F = mu * N = mu * m * g
        total_mass = self.block_mass + (self.weights_count * self.weight_mass)
        self.current_force = self.mu * total_mass * self.g

    def stop_pull(self):
        self.is_pulling = False
        self.current_force = 0.0
        self.block_x = 50

    def reset_pos(self):
        self.stop_pull()
        self.update()

    def get_total_mass_kg(self):
        return self.block_mass + (self.weights_count * self.weight_mass)

    def animate(self):
        if self.is_pulling:
            self.block_x += 2
            if self.block_x > self.width() - 250:
                self.block_x = 50
            
            target_spring = self.current_force * 20 
            self.spring_len += (target_spring - self.spring_len) * 0.1
        else:
            self.spring_len = 0
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        ground_y = h - 80

        # 1. Поверхность
        painter.fillRect(0, ground_y, w, 80, self.surface_color)
        painter.setPen(Qt.black)
        painter.drawLine(0, ground_y, w, ground_y)

        # 2. Брусок
        bx = self.block_x
        by = ground_y - 40
        bw, bh = 100, 40
        
        grad = QLinearGradient(bx, by, bx, by + bh)
        grad.setColorAt(0, QColor(139, 69, 19))
        grad.setColorAt(1, QColor(160, 82, 45))
        painter.setBrush(grad)
        painter.drawRect(int(bx), int(by), bw, bh)
        painter.setPen(Qt.white)
        painter.drawText(int(bx), int(by), bw, bh, Qt.AlignCenter, "Брусок (100г)")

        # 3. Грузы
        weight_w = 30
        weight_h = 20
        start_wx = bx + 10
        for i in range(self.weights_count):
            wx = start_wx + i * (weight_w + 5)
            wy = by - weight_h
            painter.setBrush(QColor(50, 50, 50))
            painter.setPen(Qt.black)
            painter.drawRect(int(wx), int(wy), weight_w, weight_h)

        # 4. Динамометр и Пружина
        spring_start_x = bx + bw
        spring_end_x = spring_start_x + 50 + self.spring_len
        spring_y = by + bh / 2
        
        painter.setPen(QPen(Qt.black, 2))
        path = QPainterPath()
        path.moveTo(spring_start_x, spring_y)
        steps = 10
        step_w = (spring_end_x - spring_start_x) / steps
        for i in range(1, steps + 1):
            offset = 5 if i % 2 == 0 else -5
            path.lineTo(spring_start_x + i * step_w, spring_y + offset)
        painter.drawPath(path)

        # Корпус динамометра
        dyn_x = spring_end_x
        dyn_w = 120
        dyn_h = 30
        dyn_y = spring_y - dyn_h / 2
        
        painter.setBrush(QColor(240, 240, 240))
        painter.setPen(Qt.black)
        painter.drawRect(int(dyn_x), int(dyn_y), dyn_w, dyn_h)
        
        text = f"F = {self.current_force:.2f} H" if self.is_pulling else "F = 0 H"
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(int(dyn_x), int(dyn_y), dyn_w, dyn_h, Qt.AlignCenter, text)
        
        painter.setBrush(QColor(255, 200, 150))
        painter.drawEllipse(int(dyn_x + dyn_w), int(spring_y - 10), 20, 20)


# ==========================================
# ГЛАВНОЕ ОКНО
# ==========================================
class LabFrictionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №8: Сила трения")
        self.resize(1000, 600)
        self.setup_ui()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СЛЕВА: Стенд ---
        left_group = QGroupBox("Стенд")
        left_layout = QVBoxLayout()
        self.stand = FrictionWidget()
        left_layout.addWidget(self.stand)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- СПРАВА: Управление ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Настройки
        set_g = QGroupBox("Настройки")
        set_l = QVBoxLayout()
        
        set_l.addWidget(QLabel("Тип поверхности:"))
        self.combo_surface = QComboBox()
        self.combo_surface.addItems(["Дерево (μ ≈ 0.3)", "Пластик (μ ≈ 0.15)", "Наждачка (μ ≈ 0.6)"])
        self.combo_surface.currentIndexChanged.connect(self.stand.set_surface)
        set_l.addWidget(self.combo_surface)
        
        set_l.addWidget(QLabel("Грузы (по 100г):"))
        h_btns = QHBoxLayout()
        btn_add = QPushButton("+ Груз")
        btn_add.clicked.connect(self.stand.add_weight)
        btn_rem = QPushButton("- Груз")
        btn_rem.clicked.connect(self.stand.remove_weight)
        h_btns.addWidget(btn_rem)
        h_btns.addWidget(btn_add)
        set_l.addLayout(h_btns)
        
        self.btn_pull = QPushButton("Тянуть (Измерить)")
        self.btn_pull.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 30px;")
        self.btn_pull.setCheckable(True)
        self.btn_pull.clicked.connect(self.toggle_pull)
        set_l.addWidget(self.btn_pull)
        
        set_g.setLayout(set_l)
        right_panel.addWidget(set_g)

        # 2. Ввод данных
        inp_g = QGroupBox("Вычисления")
        inp_l = QVBoxLayout()
        
        self.in_m = QLineEdit(); self.in_m.setPlaceholderText("Общая масса m (кг)")
        self.in_f = QLineEdit(); self.in_f.setPlaceholderText("Сила трения F (Н)")
        self.in_mu = QLineEdit(); self.in_mu.setPlaceholderText("Коэффициент μ")
        
        inp_l.addWidget(QLabel("Общая масса (кг):"))
        inp_l.addWidget(self.in_m)
        inp_l.addWidget(QLabel("Сила трения (Н):"))
        inp_l.addWidget(self.in_f)
        inp_l.addWidget(QLabel("Коэффициент μ = F / (mg):"))
        inp_l.addWidget(self.in_mu)
        
        btn_check = QPushButton("Проверить и Записать")
        btn_check.clicked.connect(self.check_answer)
        inp_l.addWidget(btn_check)
        
        inp_g.setLayout(inp_l)
        right_panel.addWidget(inp_g)

        # 3. Таблица
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["m (кг)", "F (Н)", "μ"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_panel.addWidget(QLabel("Результаты:"))
        right_panel.addWidget(self.table)

    def toggle_pull(self, checked):
        if checked:
            self.btn_pull.setText("Стоп")
            self.btn_pull.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; height: 30px;")
            self.stand.start_pull()
        else:
            self.btn_pull.setText("Тянуть (Измерить)")
            self.btn_pull.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 30px;")
            self.stand.stop_pull()

    def check_answer(self):
        try:
            u_m = float(self.in_m.text())
            u_f = float(self.in_f.text())
            u_mu = float(self.in_mu.text())
        except:
            QMessageBox.warning(self, "Ошибка", "Введите числа!")
            return

        real_m = self.stand.get_total_mass_kg()
        real_f = self.stand.current_force
        
        if not self.stand.is_pulling:
             QMessageBox.warning(self, "Инфо", "Сначала нажмите кнопку 'Тянуть'!")
             return

        real_mu = real_f / (real_m * 9.81)

        ok_m = abs(u_m - real_m) < 0.01
        ok_f = abs(u_f - real_f) < 0.1
        ok_mu = abs(u_mu - real_mu) < 0.05

        if ok_m and ok_f and ok_mu:
            QMessageBox.information(self, "Результат", "✅ ВЕРНО! Коэффициент найден.")
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(u_m)))
            self.table.setItem(row, 1, QTableWidgetItem(str(u_f)))
            self.table.setItem(row, 2, QTableWidgetItem(str(u_mu)))
        else:
            msg = "ЕСТЬ ОШИБКИ:\n"
            if not ok_m: msg += f"- Неверная масса (Правильно: {real_m:.3f} кг)\n"
            if not ok_f: msg += f"- Неверная сила (Смотрите на динамометр)\n"
            if not ok_mu: msg += f"- Неверный коэффициент"
            QMessageBox.warning(self, "Ошибка", msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabFrictionApp()
    win.show()
    sys.exit(app.exec())