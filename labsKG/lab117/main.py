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
        
        # КОТОРМО: Параметры перехода -> Өтүш параметрлери
        self.inputs_group = QGroupBox("Өтүш параметрлери")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        ctrl_layout.addWidget(self.inputs_group)
        
        # КОТОРМО: Результат -> Жыйынтык
        ans_box = QGroupBox("Жыйынтык")
        ans_layout = QVBoxLayout(ans_box)
        # КОТОРМО: Энергия фотона E (эВ) -> Фотондун энергиясы E (эВ)
        ans_layout.addWidget(QLabel("Фотондун энергиясы E (эВ):"))
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Мисалы: 1.89")
        ans_layout.addWidget(self.answer_input)
        
        # КОТОРМО: Проверить ответ -> Жоопту текшерүү
        self.btn_check = QPushButton("Жоопту текшерүү")
        self.btn_check.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.btn_check.clicked.connect(self.check_answer)
        ans_layout.addWidget(self.btn_check)
        ctrl_layout.addWidget(ans_box); ctrl_layout.addStretch()
        
        # Правая панель
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel)
        self.visualizer = self.create_visualizer()
        right_layout.addWidget(self.visualizer, stretch=3)
        
        self.table = QTableWidget(0, 4)
        # КОТОРМО: Заголовки таблицы
        self.table.setHorizontalHeaderLabels(["Өтүш", "Сиздин E (эВ)", "Туура E (эВ)", "Статус"])
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
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "Сан маанисин киргизиңиз."); return
            
        true_val = self.get_true_value()
        # Допуск 0.05 эВ
        is_correct = abs(user_val - true_val) <= 0.05
        
        row = self.table.rowCount(); self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(self.get_params_str()))
        self.table.setItem(row, 1, QTableWidgetItem(f"{user_val:.2f}"))
        self.table.setItem(row, 2, QTableWidgetItem(f"{true_val:.2f}"))
        
        # КОТОРМО: Статус иконки
        status = QTableWidgetItem("✅" if is_correct else "❌")
        status.setForeground(QBrush(QColor("green") if is_correct else QColor("red")))
        self.table.setItem(row, 3, status)
        
        if is_correct:
            # КОТОРМО: Успех -> Азаматсыз
            QMessageBox.information(self, "Азаматсыз", "Туура! Сиз кванттын энергиясын эсептедиңиз.")
        else:
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", f"Туура жооп: {true_val:.2f} эВ")


# --- ВИЗУАЛИЗАТОР УРОВНЕЙ ---
class AtomVisualizer(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: white; border: 1px solid #aaa;")
        self.n_level = 3 # Баштапкы деңгээл
        self.target_n = 2 # Акыркы (Бальмер сериясы)
        
        self.electron_y = 0
        self.target_y = 0
        self.t = 0.0
        self.animating = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def set_level(self, n):
        self.n_level = n
        self.animating = True 
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
        
        # Энергия деңгээлдерин тартуу
        # E_n ~ -1/n^2
        def get_y(n):
            e_val = -13.6 / (n**2)
            scale = (h - 100) / 13.6
            y = 50 + scale * abs(e_val)
            return y

        levels = [1, 2, 3, 4, 5, 6]
        cx = w // 2
        line_w = 200
        
        for n in levels:
            y = get_y(n)
            p.setPen(QPen(Qt.black, 2))
            p.drawLine(int(cx - line_w/2), int(y), int(cx + line_w/2), int(y))
            p.drawText(int(cx + line_w/2 + 10), int(y + 5), f"n={n}")
            
            if n == 1: p.drawText(int(cx - line_w/2 - 60), int(y + 5), "-13.6 эВ")
            if n == 2: p.drawText(int(cx - line_w/2 - 60), int(y + 5), "-3.4 эВ")

        # Электрондун секириги
        start_y = get_y(self.n_level)
        end_y = get_y(2)
        
        cur_y = start_y + (end_y - start_y) * self.t
        
        # Электрон
        p.setBrush(Qt.blue)
        p.drawEllipse(QPointF(cx, cur_y), 6, 6)
        
        # Фотон (толкун)
        if not self.animating and self.t >= 1.0:
            p.setPen(QPen(Qt.red, 2))
            path = []
            wave_y = cur_y
            for i in range(50):
                wx = cx + 20 + i * 3
                wy = wave_y + 10 * math.sin(i * 0.5)
                path.append(QPointF(wx, wy))
            
            p.drawPolyline(path)
            
            # Жебе
            last = path[-1]
            p.drawLine(last, QPointF(last.x()-5, last.y()-5))
            p.drawLine(last, QPointF(last.x()-5, last.y()+5))
            
            p.setPen(Qt.black)
            p.drawText(int(last.x()), int(last.y()) - 15, "hν")


# --- ЛОГИКА ЛАБОРАТОРНОЙ ---
class HydrogenLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            # КОТОРМО: 11 Класс: Спектр атома водорода -> 11-класс: Суутек атомунун спектри
            title="11-класс: Суутек атомунун спектри",
            formula="hν = E_n - E_2 = 13.6 (1/2² - 1/n²) эВ",
            description=(
                # КОТОРМО: Цель -> Максаты, Инструкция
                "<b>Максаты:</b> Бальмер сериясынын фотондорунун энергиясын эсептөө.<br>"
                "Электрон <b>n</b> деңгээлинен <b>2</b> деңгээлине өтөт.<br>"
                "1. n деңгээлин тандаңыз (3, 4, 5 же 6).<br>"
                "2. Диаграммадагы өтүштү байкаңыз.<br>"
                "3. Бөлүнүп чыккан энергияны эВ менен эсептеңиз."
            )
        )
        self.setup_inputs()

    def create_visualizer(self):
        return AtomVisualizer()

    def setup_inputs(self):
        # КОТОРМО: Начальный уровень n -> Баштапкы деңгээл n
        self.inputs_layout.addWidget(QLabel("Баштапкы деңгээл n:"))
        self.spin_n = QSpinBox()
        self.spin_n.setRange(3, 6)
        self.spin_n.setValue(3)
        self.spin_n.valueChanged.connect(self.update_level)
        self.inputs_layout.addWidget(self.spin_n)
        
        # КОТОРМО: Совершить переход -> Өтүш жасоо
        self.btn_jump = QPushButton("Өтүш жасоо")
        self.btn_jump.clicked.connect(self.animate_jump)
        self.inputs_layout.addWidget(self.btn_jump)

    def update_level(self):
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