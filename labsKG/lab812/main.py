import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QFrame,
    QDoubleSpinBox, QMessageBox, QGroupBox, QHeaderView
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QRadialGradient
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF

# --- БАЗОВЫЙ ШАБЛОН (Устранена проблема с порядком инициализации) ---
class BaseLabWindow(QWidget):
    def __init__(self, title, formula, description):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(1000, 600)
        
        main_layout = QHBoxLayout(self)
        
        # --- ЛЕВАЯ ПАНЕЛЬ (Управление) ---
        control_panel = QFrame(); control_panel.setFixedWidth(320)
        control_panel.setStyleSheet("background-color: #f5f5f5; border-right: 1px solid #ddd;")
        ctrl_layout = QVBoxLayout(control_panel)
        
        ctrl_layout.addWidget(QLabel(f"<h2>{title}</h2>"))
        formula_lbl = QLabel(f"<div style='background:#eef; padding:10px; border-radius:5px; font-size:16px; color:blue'><b>{formula}</b></div>")
        ctrl_layout.addWidget(formula_lbl)
        desc_lbl = QLabel(description); desc_lbl.setWordWrap(True); ctrl_layout.addWidget(desc_lbl)
        ctrl_layout.addWidget(QLabel("<hr>"))
        
        # Блок ввода параметров
        self.inputs_group = QGroupBox("Эксперименттин параметрлери")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        ctrl_layout.addWidget(self.inputs_group)
        
        # Блок ответа
        ans_box = QGroupBox("Жыйынтык")
        ans_layout = QVBoxLayout(ans_box)
        ans_layout.addWidget(QLabel("Эсептелген Q (Дж) маанисин киргизиңиз:"))
        self.answer_input = QLineEdit(); self.answer_input.setPlaceholderText("Мисалы: 1200")
        ans_layout.addWidget(self.answer_input)
        
        self.btn_check = QPushButton("Жоопту текшерүү")
        self.btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_check.clicked.connect(self.check_answer)
        ans_layout.addWidget(self.btn_check)
        ctrl_layout.addWidget(ans_box); ctrl_layout.addStretch()
        
        # --- ПРАВАЯ ПАНЕЛЬ (Визуализация + Таблица) ---
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel)
        
        # Важно: self.visualizer инициализируется в дочернем классе
        self.visualizer = self.create_visualizer()
        right_layout.addWidget(self.visualizer, stretch=3)
        
        # Таблица результатов
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Параметрлер (I, R, t)", "Сиздин жооп", "Туура жооп", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.table, stretch=1)
        
        main_layout.addWidget(control_panel); main_layout.addWidget(right_panel)
        # В отличие от прошлой версии, setup_inputs не вызывается здесь, 
        # а будет вызван в конце конструктора дочернего класса.

    # Заглушки для переопределения
    def create_visualizer(self): return QFrame() # Заглушка, должно быть переопределено

    def get_true_value(self): return 0
    def get_params_str(self): return ""
    def setup_inputs(self): pass

    def check_answer(self):
        try:
            user_val = float(self.answer_input.text().replace(',', '.'))
        except ValueError:
            QMessageBox.warning(self, "Ката", "Сураныч, сан маанисин киргизиңиз.")
            return
            
        true_val = self.get_true_value()
        is_correct = abs(user_val - true_val) <= (0.02 * true_val if true_val != 0 else 0.1)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(self.get_params_str()))
        self.table.setItem(row, 1, QTableWidgetItem(str(user_val)))
        self.table.setItem(row, 2, QTableWidgetItem(f"{true_val:.2f}"))
        
        status_item = QTableWidgetItem("✅ Туура" if is_correct else "❌ Ката")
        status_item.setForeground(QBrush(QColor("green") if is_correct else QColor("red")))
        self.table.setItem(row, 3, status_item)
        
        if is_correct:
            QMessageBox.information(self, "Азаматсыз!", "Эсептөө туура аткарылды.")
        else:
            QMessageBox.warning(self, "Туура эмес", f"Эсептөөдө ката бар.\nТуура жооп: {true_val:.2f}")


# --- ВИЗУАЛИЗАТОР (ОТРИСОВКА) ---
class JouleLenzVisualizer(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: white; border: 1px solid #aaa;")
        self.current = 0.0
        self.resistance = 0.0
        self.heat_level = 0.0
        self.bubbles = []
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(40)

    def update_params(self, I, R): # t удален, так как он влияет только на Q, но не на процесс нагрева в реальном времени
        self.current = I
        self.resistance = R
        self.heat_level = 0.0 
        self.bubbles = []

    def animate(self):
        power = (self.current ** 2) * self.resistance
        
        if power > 0:
            step = power / 500.0 
            self.heat_level = min(1.0, self.heat_level + step)
        else:
            self.heat_level = max(0.0, self.heat_level - 0.01)

        if self.heat_level > 0.3:
            chance = int(self.heat_level * 10)
            if random.randint(0, 20) < chance:
                self.bubbles.append([random.randint(220, 380), 350, random.uniform(1, 3), random.randint(2, 6)])

        for b in self.bubbles:
            b[1] -= b[2]
        
        self.bubbles = [b for b in self.bubbles if b[1] > 150]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx = w // 2
        
        # 1. Стакан
        glass_rect = QRectF(cx - 100, h/2 - 100, 200, 250)
        r = int(255 * self.heat_level); b = int(255 * (1.0 - self.heat_level))
        water_color = QColor(r, 0, b, 150)
        painter.setBrush(QBrush(water_color)); painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(glass_rect)
        
        # 2. Спираль (резистор)
        start_x, end_x = cx - 80, cx + 80
        y_pos = h/2 + 80
        steps = 20; step_w = (end_x - start_x) / steps
        
        glow_color = QColor(255, 100 + int((1-self.heat_level)*155), 100)
        painter.setPen(QPen(glow_color, 3 + self.current/2) if self.current > 0 else QPen(Qt.black, 2))
        
        prev_pt = QPointF(start_x, y_pos)
        for i in range(1, steps + 1):
            offset = -15 if i % 2 else 15
            curr_x = start_x + i * step_w; curr_y = y_pos + offset
            painter.drawLine(prev_pt, QPointF(curr_x, curr_y)); prev_pt = QPointF(curr_x, curr_y)
            
        # 3. Пузырьки
        painter.setBrush(Qt.white); painter.setPen(Qt.NoPen)
        for b in self.bubbles:
            bx = b[0] - 300 + cx; by = b[1] - 300 + h/2 + 50
            if glass_rect.contains(bx, by):
                painter.drawEllipse(QPointF(bx, by), b[3], b[3])
        
        # 4. Градусник (схематично)
        painter.setBrush(Qt.white); painter.setPen(Qt.black)
        painter.drawRect(glass_rect.right() + 10, glass_rect.y(), 15, 200)
        
        fill_h = 200 * (0.2 + 0.8 * self.heat_level)
        painter.setBrush(Qt.red)
        painter.drawRect(glass_rect.right() + 11, glass_rect.bottom() - fill_h, 13, fill_h)


# --- ЛОГИКА ЛАБОРАТОРНОЙ ---
class JouleLenzLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            title="8-класс: Джоуль-Ленц мыйзамы",
            formula="Q = I² · R · t",
            description=(
                "<b>Иштин максаты:</b> Өткөргүчтө бөлүнүп чыккан жылуулук санынын "
                "ток күчүнөн, каршылыктан жана убакыттан көз карандылыгын изилдөө.<br><br>"
                "<b>Ишке көрсөтмө:</b><br>"
                "1. Ток күчүн (I) жана каршылыкты (R) жөндөгүчтөрдүн жардамы менен орнотуңуз.<br>"
                "2. Токтун өтүү убактысын (t) көрсөтүңүз.<br>"
                "3. Суюктуктун жылышына (түсүнүн өзгөрүшүнө жана көбүкчөлөргө) байкоо жүргүзүңүз.<br>"
                "4. Формула боюнча Q маанисин эсептеп, 'Жоопту текшерүү' баскычын басыңыз."
            )
        )
        self.setup_inputs()

    def create_visualizer(self):
        return JouleLenzVisualizer()

    def setup_inputs(self):
        # I - Ток
        self.spin_I = QDoubleSpinBox(); self.spin_I.setRange(0, 10.0); self.spin_I.setValue(2.0)
        self.spin_I.setSuffix(" А"); self.spin_I.setPrefix("I = ")
        self.spin_I.valueChanged.connect(self.update_simulation)
        self.inputs_layout.addWidget(self.spin_I)
        
        # R - Сопротивление
        self.spin_R = QDoubleSpinBox(); self.spin_R.setRange(0, 50.0); self.spin_R.setValue(10.0)
        self.spin_R.setSuffix(" Ом"); self.spin_R.setPrefix("R = ")
        self.spin_R.valueChanged.connect(self.update_simulation)
        self.inputs_layout.addWidget(self.spin_R)
        
        # t - Время
        self.spin_t = QDoubleSpinBox(); self.spin_t.setRange(0, 100.0); self.spin_t.setValue(10.0)
        self.spin_t.setSuffix(" с"); self.spin_t.setPrefix("t = ")
        self.inputs_layout.addWidget(self.spin_t)
        
        self.update_simulation()

    def update_simulation(self):
        # Передаем только I и R в визуализатор (т.к. t влияет только на итоговое Q)
        I = self.spin_I.value()
        R = self.spin_R.value()
        self.visualizer.update_params(I, R)

    def get_true_value(self):
        I = self.spin_I.value()
        R = self.spin_R.value()
        t = self.spin_t.value()
        return (I ** 2) * R * t

    def get_params_str(self):
        return f"I={self.spin_I.value()}A, R={self.spin_R.value()}Ω, t={self.spin_t.value()}c"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JouleLenzLab()
    window.show()
    sys.exit(app.exec())