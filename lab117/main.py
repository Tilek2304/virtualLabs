import sys
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QFrame,
    QDoubleSpinBox, QMessageBox, QGroupBox, QHeaderView, QSpinBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygon
from PySide6.QtCore import Qt, QTimer, QPointF

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
        
        self.inputs_group = QGroupBox("Параметры перехода")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        ctrl_layout.addWidget(self.inputs_group)
        
        ans_box = QGroupBox("Результат")
        ans_layout = QVBoxLayout(ans_box)
        ans_layout.addWidget(QLabel("Энергия фотона E (эВ):"))
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Например: 1.89")
        ans_layout.addWidget(self.answer_input)
        
        self.btn_check = QPushButton("Проверить ответ")
        self.btn_check.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.btn_check.clicked.connect(self.check_answer)
        ans_layout.addWidget(self.btn_check)
        ctrl_layout.addWidget(ans_box); ctrl_layout.addStretch()
        
        # Правая панель
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel)
        self.visualizer = self.create_visualizer()
        right_layout.addWidget(self.visualizer, stretch=3)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Переход", "Ваш E (эВ)", "Эталон (эВ)", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.table, stretch=1)
        
        main_layout.addWidget(control_panel); main_layout.addWidget(right_panel)

    def create_visualizer(self): return QFrame()
    def get_true_value(self): return 0.0
    def get_params_str(self): return ""
    def setup_inputs(self): pass

    def check_answer(self):
        try:
            user_val = float(self.answer_input.text().replace(',', '.'))
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите число."); return
            
        true_val = self.get_true_value()
        # Допуск 0.05 эВ
        is_correct = abs(user_val - true_val) <= 0.05
        
        row = self.table.rowCount(); self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(self.get_params_str()))
        self.table.setItem(row, 1, QTableWidgetItem(f"{user_val:.2f}"))
        self.table.setItem(row, 2, QTableWidgetItem(f"{true_val:.2f}"))
        
        status = QTableWidgetItem("✅" if is_correct else "❌")
        status.setForeground(QBrush(QColor("green") if is_correct else QColor("red")))
        self.table.setItem(row, 3, status)
        
        if is_correct: QMessageBox.information(self, "Успех", "Верно! Вы рассчитали энергию кванта.")
        else: QMessageBox.warning(self, "Ошибка", f"Правильный ответ: {true_val:.2f} эВ")


# --- ВИЗУАЛИЗАТОР УРОВНЕЙ ---
class AtomVisualizer(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: white; border: 1px solid #aaa;")
        self.n_level = 3 # Начальный уровень (откуда прыгаем)
        self.target_n = 2 # Конечный (серия Бальмера)
        
        self.electron_y = 0
        self.target_y = 0
        self.t = 0.0
        self.animating = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def set_level(self, n):
        self.n_level = n
        self.animating = True # Запускаем анимацию прыжка
        self.t = 0.0

    def animate(self):
        if self.animating:
            self.t += 0.05
            if self.t > 1.0:
                self.t = 1.0
                self.animating = False
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        # Рисуем уровни энергии (ось Y инвертирована для удобства, E=0 вверху)
        # E_n ~ -1/n^2. Масштабируем на экран.
        # n=1 (осн) - самый низкий. n=inf - самый верхний.
        # Пусть n=1 это y=h-50, n=inf это y=50.
        
        def get_y(n):
            # E ~ -1/n^2. Диапазон E от -13.6 (n=1) до 0 (n=inf)
            # Нормализуем: 1/1 - 1/n^2
            # map -13.6 -> h-50, 0 -> 50
            e_val = -13.6 / (n**2)
            # Линейная интерполяция по энергии
            # y = k * e_val + b
            # h-50 = k*(-13.6) + b
            # 50 = k*(0) + b -> b = 50
            # k = (h-100) / 13.6
            scale = (h - 100) / 13.6
            y = 50 + scale * abs(e_val)
            return y

        # Рисуем уровни n=1..6
        levels = [1, 2, 3, 4, 5, 6]
        cx = w // 2
        line_w = 200
        
        for n in levels:
            y = get_y(n)
            p.setPen(QPen(Qt.black, 2))
            p.drawLine(int(cx - line_w/2), int(y), int(cx + line_w/2), int(y))
            p.drawText(int(cx + line_w/2 + 10), int(y + 5), f"n={n}")
            
            if n == 1: p.drawText(int(cx - line_w/2 - 40), int(y + 5), "-13.6 эВ")
            if n == 2: p.drawText(int(cx - line_w/2 - 40), int(y + 5), "-3.4 эВ")

        # Рисуем прыжок электрона
        start_y = get_y(self.n_level)
        end_y = get_y(2)
        
        # Текущая позиция (интерполяция)
        cur_y = start_y + (end_y - start_y) * self.t
        
        # Электрон
        p.setBrush(Qt.blue)
        p.drawEllipse(QPointF(cx, cur_y), 6, 6)
        
        # Если прыжок завершен, рисуем фотон (волну)
        if not self.animating and self.t >= 1.0:
            p.setPen(QPen(Qt.red, 2))
            # Рисуем синусоиду, вылетающую вправо
            path = []
            wave_y = cur_y
            for i in range(50):
                wx = cx + 20 + i * 3
                wy = wave_y + 10 * math.sin(i * 0.5)
                path.append(QPointF(wx, wy))
            
            p.drawPolyline(path)
            
            # Стрелка
            last = path[-1]
            p.drawLine(last, QPointF(last.x()-5, last.y()-5))
            p.drawLine(last, QPointF(last.x()-5, last.y()+5))
            
            p.setPen(Qt.black)
            p.drawText(int(last.x()), int(last.y()) - 15, "hν")


# --- ЛОГИКА ЛАБОРАТОРНОЙ ---
class HydrogenLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            title="11 Класс: Спектр атома водорода",
            formula="hν = E_n - E_2 = 13.6 (1/2² - 1/n²) эВ",
            description=(
                "<b>Цель:</b> Рассчитать энергию фотонов серии Бальмера.<br>"
                "Электрон переходит с уровня <b>n</b> на уровень <b>2</b>.<br>"
                "1. Выберите уровень n (3, 4, 5 или 6).<br>"
                "2. Наблюдайте переход на диаграмме.<br>"
                "3. Рассчитайте выделившуюся энергию в эВ."
            )
        )
        self.setup_inputs()

    def create_visualizer(self):
        return AtomVisualizer()

    def setup_inputs(self):
        self.inputs_layout.addWidget(QLabel("Начальный уровень n:"))
        self.spin_n = QSpinBox()
        self.spin_n.setRange(3, 6)
        self.spin_n.setValue(3)
        self.spin_n.valueChanged.connect(self.update_level)
        self.inputs_layout.addWidget(self.spin_n)
        
        self.btn_jump = QPushButton("Совершить переход")
        self.btn_jump.clicked.connect(self.animate_jump)
        self.inputs_layout.addWidget(self.btn_jump)

    def update_level(self):
        # Просто обновляет переменную, не прыгает
        pass

    def animate_jump(self):
        n = self.spin_n.value()
        self.visualizer.set_level(n)

    def get_true_value(self):
        n = self.spin_n.value()
        # E = 13.6 * (1/4 - 1/n^2)
        E = 13.6 * (0.25 - 1.0/(n**2))
        return E

    def get_params_str(self):
        return f"n={self.spin_n.value()} -> n=2"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = HydrogenLab()
    window.show()
    sys.exit(app.exec())