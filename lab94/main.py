import sys
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QFrame,
    QDoubleSpinBox, QMessageBox, QGroupBox, QHeaderView
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF

# --- БАЗОВЫЙ ШАБЛОН ---
class BaseLabWindow(QWidget):
    def __init__(self, title, formula, description):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(1000, 600)
        
        main_layout = QHBoxLayout(self)
        
        # Левая панель
        control_panel = QFrame(); control_panel.setFixedWidth(320)
        control_panel.setStyleSheet("background-color: #f5f5f5; border-right: 1px solid #ddd;")
        ctrl_layout = QVBoxLayout(control_panel)
        
        ctrl_layout.addWidget(QLabel(f"<h2>{title}</h2>"))
        formula_lbl = QLabel(f"<div style='background:#eef; padding:10px; border-radius:5px; font-size:16px; color:blue'><b>{formula}</b></div>")
        ctrl_layout.addWidget(formula_lbl)
        desc_lbl = QLabel(description); desc_lbl.setWordWrap(True); ctrl_layout.addWidget(desc_lbl)
        ctrl_layout.addWidget(QLabel("<hr>"))
        
        self.inputs_group = QGroupBox("Параметры маятника")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        ctrl_layout.addWidget(self.inputs_group)
        
        ans_box = QGroupBox("Результат")
        ans_layout = QVBoxLayout(ans_box)
        ans_layout.addWidget(QLabel("Рассчитайте частоту f (Гц):"))
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Например: 1.59")
        ans_layout.addWidget(self.answer_input)
        
        self.btn_check = QPushButton("Проверить ответ")
        self.btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_check.clicked.connect(self.check_answer)
        ans_layout.addWidget(self.btn_check)
        ctrl_layout.addWidget(ans_box); ctrl_layout.addStretch()
        
        # Правая панель
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel)
        self.visualizer = self.create_visualizer()
        right_layout.addWidget(self.visualizer, stretch=3)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Параметры (k, m)", "Ваш f (Гц)", "Эталон (Гц)", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.table, stretch=1)
        
        main_layout.addWidget(control_panel); main_layout.addWidget(right_panel)

    def create_visualizer(self): return QFrame()
    def get_true_value(self): return 0.0
    def get_params_str(self): return ""
    def setup_inputs(self): pass

    def check_answer(self):
        try:
            val_text = self.answer_input.text().replace(',', '.')
            if not val_text: raise ValueError
            user_val = float(val_text)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите числовое значение.")
            return
            
        true_val = self.get_true_value()
        # Допуск 5%
        is_correct = abs(user_val - true_val) <= (0.05 * true_val if true_val != 0 else 0.05)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(self.get_params_str()))
        self.table.setItem(row, 1, QTableWidgetItem(f"{user_val:.3f}"))
        self.table.setItem(row, 2, QTableWidgetItem(f"{true_val:.3f}"))
        
        status_item = QTableWidgetItem("✅ Верно" if is_correct else "❌ Ошибка")
        status_item.setForeground(QBrush(QColor("green") if is_correct else QColor("red")))
        self.table.setItem(row, 3, status_item)
        
        if is_correct:
            QMessageBox.information(self, "Успех", "Отлично! Частота найдена верно.")
        else:
            QMessageBox.warning(self, "Ошибка", f"Неверно.\nПравильный ответ: {true_val:.3f} Гц")


# --- ВИЗУАЛИЗАТОР МАЯТНИКА ---
class PendulumVisualizer(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: white; border: 1px solid #aaa;")
        self.mass = 1.0  # кг
        self.k = 20.0    # Н/м
        self.t = 0.0     # время симуляции
        
        # Таймер анимации (30 мс ~ 33 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def update_params(self, m, k):
        self.mass = m
        self.k = k
        # Не сбрасываем t полностью, чтобы не было резкого скачка, 
        # но можно сбросить фазу, если нужно.

    def animate(self):
        # Шаг времени. Можно ускорить/замедлить, умножив на коэффициент
        dt = 0.05 
        self.t += dt
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        cx = w // 2
        ceiling_y = 50
        
        # 1. Потолок
        p.setBrush(QColor(50, 50, 50))
        p.setPen(Qt.NoPen)
        p.drawRect(cx - 100, ceiling_y - 10, 200, 10)
        
        # 2. Физика колебаний
        # x(t) = A * cos(omega * t)
        # omega = sqrt(k / m)
        if self.mass > 0:
            omega = math.sqrt(self.k / self.mass)
        else:
            omega = 0
            
        amplitude = 100 # Амплитуда колебаний в пикселях
        equilibrium_y = 300 # Положение равновесия
        
        # Смещение от равновесия
        dy = amplitude * math.cos(omega * self.t)
        
        current_y = equilibrium_y + dy
        
        # 3. Пружина (Зигзаг)
        p.setPen(QPen(Qt.black, 2))
        p.setBrush(Qt.NoBrush)
        
        segments = 16 # Количество витков
        spring_length = current_y - ceiling_y
        segment_h = spring_length / segments
        
        points = []
        points.append(QPointF(cx, ceiling_y))
        
        for i in range(1, segments):
            # Чередование влево-вправо
            offset = 15 if i % 2 == 1 else -15
            py = ceiling_y + i * segment_h
            points.append(QPointF(cx + offset, py))
            
        points.append(QPointF(cx, current_y))
        
        p.drawPolyline(points)
        
        # 4. Груз
        # Размер груза визуально зависит от массы (для наглядности)
        radius = 20 + (self.mass * 3) 
        p.setBrush(QColor("#e74c3c"))
        p.setPen(QPen(Qt.black, 2))
        
        # Рисуем шар с центром в (cx, current_y + radius)
        p.drawEllipse(QPointF(cx, current_y + radius), radius, radius)
        
        # Текст на грузе
        p.setPen(Qt.white)
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.drawText(QRectF(cx - radius, current_y, radius*2, radius*2), 
                   Qt.AlignCenter, f"{self.mass} кг")

        # 5. Инфо
        p.setPen(Qt.black)
        p.drawText(10, 20, f"Время t: {self.t:.2f} с")
        # Для отладки/учителя можно вывести omega
        # p.drawText(10, 40, f"ω: {omega:.2f} рад/с")


# --- ЛОГИКА ЛАБОРАТОРНОЙ ---
class PendulumFreqLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            title="9 Класс: Пружинный маятник (Частота)",
            formula="f = (1 / 2π) · √(k / m)",
            description=(
                "<b>Цель:</b> Определить частоту свободных колебаний пружинного маятника.<br>"
                "<b>k</b> — жесткость пружины (Н/м).<br>"
                "<b>m</b> — масса груза (кг).<br>"
                "Обратите внимание: чем больше жесткость, тем быстрее колебания. Чем больше масса, тем они медленнее."
            )
        )
        self.setup_inputs()

    def create_visualizer(self):
        return PendulumVisualizer()

    def setup_inputs(self):
        # Жесткость k
        self.inputs_layout.addWidget(QLabel("Жесткость пружины k (Н/м):"))
        self.spin_k = QDoubleSpinBox()
        self.spin_k.setRange(1, 200)
        self.spin_k.setValue(20)
        self.spin_k.setSuffix(" Н/м")
        self.inputs_layout.addWidget(self.spin_k)
        
        # Масса m
        self.inputs_layout.addWidget(QLabel("Масса груза m (кг):"))
        self.spin_m = QDoubleSpinBox()
        self.spin_m.setRange(0.1, 20.0)
        self.spin_m.setValue(1.0)
        self.spin_m.setSingleStep(0.1)
        self.spin_m.setSuffix(" кг")
        self.inputs_layout.addWidget(self.spin_m)
        
        # Обновление
        self.spin_k.valueChanged.connect(self.update_simulation)
        self.spin_m.valueChanged.connect(self.update_simulation)
        
        self.update_simulation()

    def update_simulation(self):
        m = self.spin_m.value()
        k = self.spin_k.value()
        self.visualizer.update_params(m, k)

    def get_true_value(self):
        m = self.spin_m.value()
        k = self.spin_k.value()
        # f = 1/2pi * sqrt(k/m)
        if m == 0: return 0
        return (1 / (2 * math.pi)) * math.sqrt(k / m)

    def get_params_str(self):
        return f"k={self.spin_k.value()}, m={self.spin_m.value()}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PendulumFreqLab()
    window.show()
    sys.exit(app.exec())