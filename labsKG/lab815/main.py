import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QFrame,
    QDoubleSpinBox, QMessageBox, QGroupBox, QHeaderView, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygon
from PySide6.QtCore import Qt, QTimer, QPoint

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
        
        # КОТОРМО: Управление цепью -> Чынжырды башкаруу
        self.inputs_group = QGroupBox("Чынжырды башкаруу")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        ctrl_layout.addWidget(self.inputs_group)
        
        # КОТОРМО: Результат -> Жыйынтык
        ans_box = QGroupBox("Жыйынтык")
        ans_layout = QVBoxLayout(ans_box)
        # КОТОРМО: Общее сопротивление R -> Жалпы каршылык R (Ом)
        ans_layout.addWidget(QLabel("Жалпы каршылык R (Ом):"))
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Мисалы: 5.0")
        ans_layout.addWidget(self.answer_input)
        
        # КОТОРМО: Проверить ответ -> Жоопту текшерүү
        self.btn_check = QPushButton("Жоопту текшерүү")
        self.btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_check.clicked.connect(self.check_answer)
        ans_layout.addWidget(self.btn_check)
        ctrl_layout.addWidget(ans_box); ctrl_layout.addStretch()
        
        # Правая панель
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel)
        self.visualizer = self.create_visualizer()
        right_layout.addWidget(self.visualizer, stretch=3)
        
        self.table = QTableWidget(0, 4)
        # КОТОРМО: Заголовки таблицы
        self.table.setHorizontalHeaderLabels(["R1, R2, R3 (Ом)", "Сиздин R (Ом)", "Туура R (Ом)", "Статус"])
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
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "Сан маанисин киргизиңиз.")
            return
            
        true_val = self.get_true_value()
        # Допуск 5%
        is_correct = abs(user_val - true_val) <= (0.05 * true_val if true_val != 0 else 0.1)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(self.get_params_str()))
        self.table.setItem(row, 1, QTableWidgetItem(f"{user_val:.2f}"))
        self.table.setItem(row, 2, QTableWidgetItem(f"{true_val:.2f}"))
        
        # КОТОРМО: Верно/Ошибка -> Туура/Ката
        status_item = QTableWidgetItem("✅ Туура" if is_correct else "❌ Ката")
        status_item.setForeground(QBrush(QColor("green") if is_correct else QColor("red")))
        self.table.setItem(row, 3, status_item)
        
        if is_correct:
            # КОТОРМО: Успех -> Азаматсыз
            QMessageBox.information(self, "Азаматсыз", "Эсептөө туура аткарылды!")
        else:
            # КОТОРМО: Ошибка -> Ката, Неверно -> Туура эмес
            QMessageBox.warning(self, "Ката", f"Туура эмес.\nТуура жооп: {true_val:.2f} Ом")


# --- ВИЗУАЛИЗАТОР СХЕМЫ ---
class CircuitVisualizer(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: white; border: 1px solid #aaa;")
        # Список резисторов
        self.resistors = [
            {'enabled': True, 'R': 10.0},
            {'enabled': True, 'R': 20.0},
            {'enabled': False, 'R': 30.0}
        ]
        self.voltage = 12.0 

    def update_resistor(self, index, enabled, resistance):
        self.resistors[index]['enabled'] = enabled
        self.resistors[index]['R'] = resistance
        self.update()

    def draw_resistor(self, p, x, y, r_val, label):
        rect_w, rect_h = 60, 20
        p.setBrush(QColor("#ddd"))
        p.setPen(QPen(Qt.black, 2))
        p.drawRect(x - rect_w/2, y - rect_h/2, rect_w, rect_h)
        
        p.setPen(Qt.black)
        p.setFont(QFont("Arial", 9))
        p.drawText(int(x - rect_w/2), int(y - 15), f"{label} = {r_val} Ом")
        
        i_branch = self.voltage / r_val
        p.setPen(QColor("blue"))
        p.drawText(int(x - rect_w/2), int(y + 25), f"I = {i_branch:.2f} A")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        cx = w // 2
        cy = h // 2
        
        top_wire_y = cy - 100
        bot_wire_y = cy + 100
        
        schema_w = 400
        start_x = cx - schema_w // 2
        end_x = cx + schema_w // 2
        
        # 1. Ток булагы
        p.setPen(QPen(Qt.black, 3))
        p.drawLine(start_x, top_wire_y, start_x, cy - 20) # +
        p.drawLine(start_x, bot_wire_y, start_x, cy + 20) # -
        
        p.drawLine(start_x - 15, cy - 20, start_x + 15, cy - 20) 
        p.drawLine(start_x - 8, cy + 20, start_x + 8, cy + 20)   
        # КОТОРМО: U=12В
        p.drawText(start_x - 40, cy, "U=12В")
        
        # 2. Негизги зымдар
        p.drawLine(start_x, top_wire_y, end_x, top_wire_y)
        p.drawLine(start_x, bot_wire_y, end_x, bot_wire_y)
        
        # 3. Тармакталыштар
        branch_spacing = schema_w / 4
        
        total_current = 0.0
        
        for i, res in enumerate(self.resistors):
            bx = start_x + branch_spacing * (i + 1)
            
            p.setPen(QPen(Qt.black, 2))
            
            if res['enabled']:
                p.drawLine(bx, top_wire_y, bx, bot_wire_y)
                self.draw_resistor(p, bx, cy, res['R'], f"R{i+1}")
                total_current += self.voltage / res['R']
                
                p.setBrush(Qt.black)
                p.drawEllipse(QPoint(int(bx), int(top_wire_y)), 3, 3)
                p.drawEllipse(QPoint(int(bx), int(bot_wire_y)), 3, 3)
            else:
                p.setPen(QPen(QColor("#aaa"), 1, Qt.DashLine))
                p.drawLine(bx, top_wire_y, bx, bot_wire_y)
                p.setPen(Qt.red)
                # КОТОРМО: Отключено -> Өчүрүлгөн
                p.drawText(int(bx)-20, int(cy), "Өчүрүлгөн")

        # 4. Жалпы ток (Амперметр)
        am_x = start_x + 60
        p.setBrush(Qt.white)
        p.setPen(QPen(Qt.black, 2))
        p.drawEllipse(QPoint(int(am_x), int(top_wire_y)), 15, 15)
        p.drawText(int(am_x)-5, int(top_wire_y)+5, "A")
        
        p.setFont(QFont("Arial", 11, QFont.Bold))
        p.setPen(QColor("darkBlue"))
        # КОТОРМО: I общ -> I жалпы
        p.drawText(int(start_x), int(top_wire_y) - 20, f"I жалпы = {total_current:.2f} A")


# --- ГЛАВНЫЙ КЛАСС ЛАБОРАТОРНОЙ ---
class ParallelLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            # КОТОРМО: 8 Класс: Параллельное соединение -> 8-класс: Өткөргүчтөрдү жарыш туташтыруу
            title="8-класс: Өткөргүчтөрдү жарыш туташтыруу",
            formula="1/R = 1/R1 + 1/R2 + ...",
            description=(
                # КОТОРМО: Цель -> Максаты, Инструкция
                "<b>Максаты:</b> Жарыш туташтыруунун касиеттерин үйрөнүү.<br>"
                "Бул туташтырууда бардык тармактардагы чыңалуу бирдей, ал эми ток күчтөрү кошулат. "
                "Чынжырдын жалпы каршылыгы эң кичине каршылыктан да <b>кичине</b> болот."
            )
        )
        self.setup_inputs()

    def create_visualizer(self):
        return CircuitVisualizer()

    def setup_inputs(self):
        # R1
        row1 = QHBoxLayout()
        # КОТОРМО: Включить -> Күйгүзүү
        self.chk_r1 = QCheckBox("R1 күйгүзүү"); self.chk_r1.setChecked(True)
        self.spin_r1 = QDoubleSpinBox(); self.spin_r1.setRange(1, 100); self.spin_r1.setValue(10); self.spin_r1.setSuffix(" Ом")
        row1.addWidget(self.chk_r1); row1.addWidget(self.spin_r1)
        self.inputs_layout.addLayout(row1)
        
        # R2
        row2 = QHBoxLayout()
        self.chk_r2 = QCheckBox("R2 күйгүзүү"); self.chk_r2.setChecked(True)
        self.spin_r2 = QDoubleSpinBox(); self.spin_r2.setRange(1, 100); self.spin_r2.setValue(20); self.spin_r2.setSuffix(" Ом")
        row2.addWidget(self.chk_r2); row2.addWidget(self.spin_r2)
        self.inputs_layout.addLayout(row2)
        
        # R3
        row3 = QHBoxLayout()
        self.chk_r3 = QCheckBox("R3 күйгүзүү"); self.chk_r3.setChecked(False)
        self.spin_r3 = QDoubleSpinBox(); self.spin_r3.setRange(1, 100); self.spin_r3.setValue(30); self.spin_r3.setSuffix(" Ом")
        row3.addWidget(self.chk_r3); row3.addWidget(self.spin_r3)
        self.inputs_layout.addLayout(row3)
        
        for w in [self.chk_r1, self.chk_r2, self.chk_r3, self.spin_r1, self.spin_r2, self.spin_r3]:
            if isinstance(w, QCheckBox): w.stateChanged.connect(self.update_simulation)
            if isinstance(w, QDoubleSpinBox): w.valueChanged.connect(self.update_simulation)
            
        self.update_simulation()

    def update_simulation(self):
        self.visualizer.update_resistor(0, self.chk_r1.isChecked(), self.spin_r1.value())
        self.visualizer.update_resistor(1, self.chk_r2.isChecked(), self.spin_r2.value())
        self.visualizer.update_resistor(2, self.chk_r3.isChecked(), self.spin_r3.value())

    def get_true_value(self):
        conductance = 0.0
        active_count = 0
        
        if self.chk_r1.isChecked():
            conductance += 1.0 / self.spin_r1.value()
            active_count += 1
        if self.chk_r2.isChecked():
            conductance += 1.0 / self.spin_r2.value()
            active_count += 1
        if self.chk_r3.isChecked():
            conductance += 1.0 / self.spin_r3.value()
            active_count += 1
            
        if active_count == 0 or conductance == 0:
            return 0.0 
            
        return 1.0 / conductance

    def get_params_str(self):
        s = []
        if self.chk_r1.isChecked(): s.append(f"R1={self.spin_r1.value()}")
        if self.chk_r2.isChecked(): s.append(f"R2={self.spin_r2.value()}")
        if self.chk_r3.isChecked(): s.append(f"R3={self.spin_r3.value()}")
        # КОТОРМО: Разомкнута -> Ачык (чынжыр)
        return ", ".join(s) if s else "Ачык"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ParallelLab()
    window.show()
    sys.exit(app.exec())