import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox,
    QTextEdit, QSizePolicy
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath, QLinearGradient, QRadialGradient
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Мензурка
# ==========================================
class MenzurkaWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(350, 500)
        self.setStyleSheet("background-color: #f4f4f4; border: 1px solid #aaa; border-radius: 8px;")

        # Параметры анимации
        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(30) # 30 мс

        # Состояние (0 = вверху, 1 = опускается, 2 = внизу, 3 = поднимается)
        self.state = 0
        self.anim_t = 0.0 # 0.0 ... 1.0 (интерполяция)
        self.anim_speed = 0.02

        self.generate_parameters()

    def generate_parameters(self):
        """Генерация новых параметров эксперимента"""
        self.V_total = random.randint(200, 500)
        self.divisions = random.choice([10, 20, 25])
        
        # Объём тела (чтобы помещалось)
        max_body = int(self.V_total * 0.3)
        self.V_body = random.randint(20, max_body)
        
        # Начальный объём жидкости
        max_liquid = self.V_total - self.V_body - 10
        self.V1 = random.randint(30, max_liquid)
        
        # Сброс анимации
        self.state = 0
        self.anim_t = 0.0
        self.update()

    def on_timer(self):
        # Волна на поверхности
        self.phase += 0.15
        if self.phase > 2 * math.pi:
            self.phase -= 2 * math.pi

        # Движение тела
        if self.state == 1: # Опускание
            self.anim_t += self.anim_speed
            if self.anim_t >= 1.0:
                self.anim_t = 1.0
                self.state = 2
        elif self.state == 3: # Поднятие
            self.anim_t -= self.anim_speed
            if self.anim_t <= 0.0:
                self.anim_t = 0.0
                self.state = 0
        
        self.update()

    def start_lower(self):
        if self.state == 0: self.state = 1
    
    def start_raise(self):
        if self.state == 2: self.state = 3

    def get_current_volume(self):
        # V_current = V1 + (V_body * t)
        return self.V1 + self.V_body * self.anim_t

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        
        # Размеры цилиндра
        cyl_w = int(w * 0.4)
        cyl_h = int(h * 0.8)
        cyl_x = int((w - cyl_w) / 2)
        cyl_y = int(h * 0.1)

        # 1. Стекло (Фон)
        grad_glass = QLinearGradient(cyl_x, 0, cyl_x + cyl_w, 0)
        grad_glass.setColorAt(0, QColor(220, 230, 240, 100))
        grad_glass.setColorAt(0.5, QColor(255, 255, 255, 150))
        grad_glass.setColorAt(1, QColor(220, 230, 240, 100))
        
        painter.setPen(QPen(Qt.gray, 2))
        painter.setBrush(grad_glass)
        painter.drawRect(cyl_x, cyl_y, cyl_w, cyl_h)

        # 2. Жидкость
        inner_x = cyl_x + 5
        inner_w = cyl_w - 10
        inner_y = cyl_y + 5
        inner_h = cyl_h - 10
        
        current_v = self.get_current_volume()
        ratio = current_v / self.V_total
        liquid_h = inner_h * ratio
        liquid_top_y = inner_y + inner_h - liquid_h

        # Путь жидкости с волной
        path = QPainterPath()
        path.moveTo(inner_x, inner_y + inner_h) 
        path.lineTo(inner_x, liquid_top_y)      
        
        steps = 20
        wave_amp = 3
        for i in range(steps + 1):
            t = i / steps
            x = inner_x + t * inner_w
            y = liquid_top_y + math.sin(self.phase + t * 4 * math.pi) * wave_amp
            path.lineTo(x, y)
            
        path.lineTo(inner_x + inner_w, inner_y + inner_h) 
        path.closeSubpath()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 150, 255, 180)) 
        painter.drawPath(path)
        
        # 3. Шкала
        painter.setPen(QPen(Qt.black, 1))
        font = QFont("Arial", 9)
        painter.setFont(font)
        
        for i in range(self.divisions + 1):
            val = int(i * (self.V_total / self.divisions))
            y_pos = inner_y + inner_h - (i / self.divisions) * inner_h
            
            painter.drawLine(inner_x, int(y_pos), inner_x + 15, int(y_pos))
            painter.drawText(inner_x + 20, int(y_pos) + 5, str(val))

        # 4. Тело
        body_r = min(30, inner_w // 3)
        
        # Позиция тела
        fixed_start_y = inner_y + 40
        end_y = liquid_top_y + body_r + 10 
        
        body_y = fixed_start_y + (end_y - fixed_start_y) * self.anim_t
        body_x = inner_x + inner_w / 2
        
        # Нить
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(int(body_x), int(cyl_y - 20), int(body_x), int(body_y))
        
        # Само тело
        grad_body = QRadialGradient(body_x - 5, body_y - 5, body_r)
        grad_body.setColorAt(0, QColor(255, 100, 100))
        grad_body.setColorAt(1, QColor(150, 50, 50))
        painter.setBrush(grad_body)
        painter.setPen(QPen(Qt.black, 1))
        painter.drawEllipse(QPointF(body_x, body_y), body_r, body_r)
        
        # Подсказки V1, V2
        if self.state == 2: # Внизу
             painter.setPen(QPen(Qt.darkGreen, 1, Qt.DashLine))
             painter.drawLine(inner_x, int(liquid_top_y), inner_x + inner_w, int(liquid_top_y))
             painter.drawText(inner_x + inner_w + 5, int(liquid_top_y), "V2")
        elif self.state == 0: # Вверху
             painter.setPen(QPen(Qt.darkBlue, 1, Qt.DashLine))
             painter.drawLine(inner_x, int(liquid_top_y), inner_x + inner_w, int(liquid_top_y))
             painter.drawText(inner_x + inner_w + 5, int(liquid_top_y), "V1")

# ==========================================
# ГЛАВНОЕ ОКНО
# ==========================================
class Lab04App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная №4: Определение объема")
        self.resize(1000, 600)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # --- СЛЕВА: Мензурка ---
        left_group = QGroupBox("Лабораторный стенд")
        left_layout = QVBoxLayout()
        self.menzurka = MenzurkaWidget()
        left_layout.addWidget(self.menzurka)
        
        # Кнопки движения
        move_layout = QHBoxLayout()
        self.btn_lower = QPushButton("Опустить")
        self.btn_lower.clicked.connect(self.menzurka.start_lower)
        self.btn_raise = QPushButton("Поднять")
        self.btn_raise.clicked.connect(self.menzurka.start_raise)
        
        move_layout.addWidget(self.btn_lower)
        move_layout.addWidget(self.btn_raise)
        left_layout.addLayout(move_layout)
        
        left_group.setLayout(left_layout)
        main_layout.addWidget(left_group, stretch=2)

        # --- СПРАВА: Управление ---
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, stretch=1)

        # 1. Задание
        task_group = QGroupBox("Задание")
        task_layout = QVBoxLayout()
        info = QLabel(
            "1. Запишите начальный объем жидкости (V1).\n"
            "2. Опустите тело в воду.\n"
            "3. Определите новый объем (V2).\n"
            "4. Вычислите объем тела: V = V2 - V1."
        )
        info.setWordWrap(True)
        task_layout.addWidget(info)
        task_group.setLayout(task_layout)
        right_panel.addWidget(task_group)

        # 2. Ввод
        input_group = QGroupBox("Ввод ответов")
        input_layout = QVBoxLayout()
        
        self.inp_v1 = QLineEdit()
        self.inp_v1.setPlaceholderText("V1 (мл)")
        
        self.inp_v2 = QLineEdit()
        self.inp_v2.setPlaceholderText("V2 (мл)")
        
        self.inp_v = QLineEdit()
        self.inp_v.setPlaceholderText("V = V2 - V1")
        
        input_layout.addWidget(QLabel("Начальный объем (V1):"))
        input_layout.addWidget(self.inp_v1)
        input_layout.addWidget(QLabel("Конечный объем (V2):"))
        input_layout.addWidget(self.inp_v2)
        input_layout.addWidget(QLabel("Объем тела (V):"))
        input_layout.addWidget(self.inp_v)
        
        input_group.setLayout(input_layout)
        right_panel.addWidget(input_group)

        # 3. Кнопки
        ctrl_group = QGroupBox("Управление")
        ctrl_layout = QVBoxLayout()
        
        self.btn_check = QPushButton("Проверить")
        self.btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 35px;")
        self.btn_check.clicked.connect(self.check_answer)
        
        self.btn_new = QPushButton("Новое задание")
        self.btn_new.clicked.connect(self.new_task)
        
        ctrl_layout.addWidget(self.btn_check)
        ctrl_layout.addWidget(self.btn_new)
        ctrl_group.setLayout(ctrl_layout)
        right_panel.addWidget(ctrl_group)

        # 4. Лог
        res_group = QGroupBox("Журнал")
        res_layout = QVBoxLayout()
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #f9f9f9; font-family: Consolas;")
        res_layout.addWidget(self.txt_log)
        res_group.setLayout(res_layout)
        right_panel.addWidget(res_group, stretch=1)

    def new_task(self):
        self.menzurka.generate_parameters()
        self.inp_v1.clear()
        self.inp_v2.clear()
        self.inp_v.clear()
        self.txt_log.append("--- Новое задание получено ---")

    def check_answer(self):
        try:
            u_v1 = float(self.inp_v1.text())
            u_v2 = float(self.inp_v2.text())
            u_v = float(self.inp_v.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите числа во все поля!")
            return

        # Правильные значения
        real_v1 = self.menzurka.V1
        real_v2 = self.menzurka.V1 + self.menzurka.V_body
        real_v = self.menzurka.V_body
        
        # Допуск погрешности (половина цены деления)
        tolerance = (self.menzurka.V_total / self.menzurka.divisions) / 2
        
        is_v1 = abs(u_v1 - real_v1) <= tolerance
        is_v2 = abs(u_v2 - real_v2) <= tolerance
        is_v = abs(u_v - real_v) <= tolerance
        
        self.txt_log.append(f"Ввод: V1={u_v1}, V2={u_v2}, V={u_v}")
        
        if is_v1 and is_v2 and is_v:
             self.txt_log.append("<span style='color:green'><b>✅ ВСЕ ВЕРНО!</b></span>")
        else:
             self.txt_log.append("<span style='color:red'><b>❌ ЕСТЬ ОШИБКИ:</b></span>")
             if not is_v1: self.txt_log.append(f"V1 неверно (Верно: ~{real_v1})")
             if not is_v2: self.txt_log.append(f"V2 неверно (Верно: ~{real_v2})")
             if not is_v: self.txt_log.append(f"V неверно (Верно: ~{real_v})")
        
        self.txt_log.append("-" * 20)
        self.txt_log.verticalScrollBar().setValue(self.txt_log.verticalScrollBar().maximum())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = Lab04App()
    win.show()
    sys.exit(app.exec())