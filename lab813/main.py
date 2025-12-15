import sys
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QFrame,
    QDoubleSpinBox, QMessageBox, QGroupBox, QHeaderView
)
# ИСПРАВЛЕНИЕ: Добавлен QPolygon
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygon
# ИСПРАВЛЕНИЕ: Добавлен QPoint
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QPoint

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
        
        self.inputs_group = QGroupBox("Параметры эксперимента")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        ctrl_layout.addWidget(self.inputs_group)
        
        ans_box = QGroupBox("Результат"); ans_layout = QVBoxLayout(ans_box)
        ans_layout.addWidget(QLabel("Введите КПД (%):"))
        self.answer_input = QLineEdit(); self.answer_input.setPlaceholderText("Например: 75.5")
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
        self.table.setHorizontalHeaderLabels(["Параметры (Aп, Aз)", "Ваш ответ (%)", "Эталон (%)", "Статус"])
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
        is_correct = abs(user_val - true_val) <= 2.0
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(self.get_params_str()))
        self.table.setItem(row, 1, QTableWidgetItem(f"{user_val:.1f}%"))
        self.table.setItem(row, 2, QTableWidgetItem(f"{true_val:.1f}%"))
        
        status_item = QTableWidgetItem("✅ Верно" if is_correct else "❌ Ошибка")
        status_item.setForeground(QBrush(QColor("green") if is_correct else QColor("red")))
        self.table.setItem(row, 3, status_item)
        
        if is_correct:
            QMessageBox.information(self, "Успех", "Отлично! КПД рассчитан верно.")
        else:
            QMessageBox.warning(self, "Ошибка", f"Неверно. Правильный КПД: {true_val:.1f}%")


# --- ВИЗУАЛИЗАТОР (БЛОК С ГРУЗОМ) ---
class BlockVisualizer(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #e6e6fa; border: 1px solid #aaa;")
        self.A_useful = 100.0
        self.A_spent = 150.0
        self.efficiency = 0.0
        self.t = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(40)

    def update_params(self, Au, As):
        self.A_useful = Au
        self.A_spent = As
        if As > 0:
            self.efficiency = (Au / As) * 100.0
        else:
            self.efficiency = 0.0

    def animate(self):
        self.t += 0.1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        cx = w // 2
        
        # 1. Потолок и шток
        painter.setBrush(QColor(80, 80, 80))
        painter.drawRect(cx - 50, 0, 100, 20)
        painter.drawLine(cx, 20, cx, 60)
        
        # 2. Блок (колесо)
        radius = 40
        center_y = 60 + radius
        painter.setBrush(QColor(200, 200, 200))
        painter.setPen(QPen(Qt.black, 3))
        painter.drawEllipse(QPointF(cx, center_y), radius, radius)
        painter.setBrush(Qt.black)
        painter.drawEllipse(QPointF(cx, center_y), 5, 5)
        
        # 3. Анимация (синус)
        offset = 30 * math.sin(self.t) 
        
        # Левая часть (Груз)
        rope_left_x = cx - radius
        # Груз движется вверх-вниз
        load_y = center_y + 150 - offset 
        
        painter.setPen(QPen(Qt.black, 3))
        painter.drawLine(QPointF(rope_left_x, center_y), QPointF(rope_left_x, load_y))
        
        painter.setBrush(QColor("#3498db"))
        painter.drawRect(QRectF(rope_left_x - 25, load_y, 50, 50))
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(QRectF(rope_left_x - 25, load_y, 50, 50), Qt.AlignCenter, "Груз\n(Aп)")
        
        # Правая часть (Сила)
        rope_right_x = cx + radius
        # Рука движется в противофазе
        pull_y = center_y + 150 + offset
        
        painter.setPen(QPen(Qt.black, 3))
        painter.drawLine(QPointF(rope_right_x, center_y), QPointF(rope_right_x, pull_y))
        
        # Стрелка силы (Красная)
        painter.setBrush(QColor("#e74c3c"))
        painter.setPen(Qt.black)
        
        # Рисуем треугольник стрелки с помощью QPolygon
        p1 = QPointF(rope_right_x, pull_y + 20).toPoint()
        p2 = QPointF(rope_right_x - 10, pull_y).toPoint()
        p3 = QPointF(rope_right_x + 10, pull_y).toPoint()
        
        arrow_head = QPolygon([p1, p2, p3])
        painter.drawPolygon(arrow_head)
        
        painter.drawText(int(rope_right_x) + 15, int(pull_y) + 10, "F (Aз)")

        # # 4. Шкала КПД
        # bar_x = cx - 100
        # bar_y = h - 50
        # bar_w = 200
        # bar_h = 30
        
        # painter.setPen(Qt.black)
        # painter.setBrush(Qt.white)
        # painter.drawRect(bar_x, bar_y, bar_w, bar_h)
        
        # fill_w = bar_w * (self.efficiency / 100.0)
        # fill_w = max(0, min(bar_w, fill_w)) # защита от выхода за границы
        
        # if self.efficiency < 50: c = QColor("#e74c3c")
        # elif self.efficiency < 80: c = QColor("#f1c40f")
        # else: c = QColor("#2ecc71")
        
        # painter.setBrush(c)
        # painter.drawRect(QRectF(bar_x, bar_y, fill_w, bar_h))
        
        # painter.setPen(Qt.black)
        # painter.drawText(QRectF(bar_x, bar_y, bar_w, bar_h), Qt.AlignCenter, f"КПД = {self.efficiency:.1f}%")


# --- ГЛАВНЫЙ КЛАСС ЛАБОРАТОРНОЙ ---
class EfficiencyLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            title="8 Класс: Определение КПД",
            formula="η = (A_полезн / A_затрач) · 100%",
            description=(
                "<b>Цель:</b> Определить КПД подвижного блока.<br>"
                "Введите значения полезной работы (подъем груза) и затраченной работы (вытягивание веревки), "
                "чтобы рассчитать эффективность механизма."
            )
        )
        self.setup_inputs()

    def create_visualizer(self):
        return BlockVisualizer()

    def setup_inputs(self):
        self.spin_Au = QDoubleSpinBox(); self.spin_Au.setRange(0, 5000); self.spin_Au.setValue(200)
        self.spin_Au.setSuffix(" Дж"); self.spin_Au.setPrefix("A пол. = ")
        self.inputs_layout.addWidget(self.spin_Au)
        
        self.spin_As = QDoubleSpinBox(); self.spin_As.setRange(1, 5000); self.spin_As.setValue(250)
        self.spin_As.setSuffix(" Дж"); self.spin_As.setPrefix("A зат. = ")
        self.inputs_layout.addWidget(self.spin_As)
        
        self.spin_Au.valueChanged.connect(self.update_simulation)
        self.spin_As.valueChanged.connect(self.update_simulation)
        self.update_simulation()

    def update_simulation(self):
        Au = self.spin_Au.value()
        As = self.spin_As.value()
        self.visualizer.update_params(Au, As)

    def get_true_value(self):
        Au = self.spin_Au.value()
        As = self.spin_As.value()
        if As == 0: return 0.0
        return (Au / As) * 100.0

    def get_params_str(self):
        return f"Aп={self.spin_Au.value()}Дж, Aз={self.spin_As.value()}Дж"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = EfficiencyLab()
    window.show()
    sys.exit(app.exec())