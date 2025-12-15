import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QFrame,
    QDoubleSpinBox, QMessageBox, QGroupBox, QHeaderView, QComboBox, QSlider
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient
from PySide6.QtCore import Qt, QTimer, QRectF

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
        
        # КОТОРМО: Параметры проводника -> Өткөргүчтүн параметрлери
        self.inputs_group = QGroupBox("Өткөргүчтүн параметрлери")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        ctrl_layout.addWidget(self.inputs_group)
        
        # КОТОРМО: Результат -> Жыйынтык
        ans_box = QGroupBox("Жыйынтык")
        ans_layout = QVBoxLayout(ans_box)
        # КОТОРМО: Рассчитайте сопротивление R -> Каршылык R (Ом) эсептеңиз:
        ans_layout.addWidget(QLabel("Каршылык R (Ом) эсептеңиз:"))
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Мисалы: 0.55")
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
        self.table.setHorizontalHeaderLabels(["Параметрлер (Мат, L, S)", "Сиздин R (Ом)", "Туура R (Ом)", "Статус"])
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
        is_correct = abs(user_val - true_val) <= (0.05 * true_val if true_val != 0 else 0.01)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(self.get_params_str()))
        self.table.setItem(row, 1, QTableWidgetItem(f"{user_val:.3f}"))
        self.table.setItem(row, 2, QTableWidgetItem(f"{true_val:.3f}"))
        
        # КОТОРМО: Верно/Ошибка -> Туура/Ката
        status_item = QTableWidgetItem("✅ Туура" if is_correct else "❌ Ката")
        status_item.setForeground(QBrush(QColor("green") if is_correct else QColor("red")))
        self.table.setItem(row, 3, status_item)
        
        if is_correct:
            # КОТОРМО: Успех -> Азаматсыз
            QMessageBox.information(self, "Азаматсыз", "Туура! Сиз каршылыктын көз карандылыгын өздөштүрдүңүз.")
        else:
            # КОТОРМО: Ошибка -> Ката, Неверно -> Туура эмес
            QMessageBox.warning(self, "Ката", f"Туура эмес.\nТуура жооп: {true_val:.4f} Ом")


# --- ВИЗУАЛИЗАТОР ПРОВОДНИКА ---
class WireVisualizer(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: white; border: 1px solid #aaa;")
        self.L = 1.0  # м
        self.S = 1.0  # мм²
        self.rho = 0.017 # Жез
        self.material_name = "Жез"
        self.color = QColor("#B87333") 

    def update_params(self, L, S, material_data):
        self.L = L
        self.S = S
        self.rho = material_data['rho']
        self.color = material_data['color']
        self.material_name = material_data['name']
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w_widget = self.width()
        h_widget = self.height()
        cx = w_widget // 2
        cy = h_widget // 2

        # Визуализация масштабы
        draw_width = 50 + (self.L / 10.0) * (w_widget - 100)
        draw_height = 10 + (self.S / 5.0) * 40
        
        rect = QRectF(cx - draw_width/2, cy - draw_height/2, draw_width, draw_height)
        
        # Градиент
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        base = self.color
        gradient.setColorAt(0, base.darker(150))
        gradient.setColorAt(0.5, base.lighter(130))
        gradient.setColorAt(1, base.darker(150))
        
        p.setBrush(QBrush(gradient))
        p.setPen(QPen(Qt.black, 1))
        p.drawRect(rect)
        
        # Өлчөмдөр
        p.setPen(QPen(Qt.black, 2))
        
        # Узундук сызыгы
        line_y = rect.bottom() + 20
        p.drawLine(rect.left(), line_y, rect.right(), line_y)
        p.drawLine(rect.left(), line_y - 5, rect.left(), line_y + 5)
        p.drawLine(rect.right(), line_y - 5, rect.right(), line_y + 5)
        p.setFont(QFont("Arial", 10))
        # КОТОРМО: м
        p.drawText(cx - 20, int(line_y) + 20, f"L = {self.L} м")
        
        # Аянт сызыгы
        # КОТОРМО: мм²
        p.setFont(QFont("Arial", 10))
        p.drawText(rect.right() + 10, cy, f"S = {self.S} мм²")
        
        # Материал текст
        p.setFont(QFont("Arial", 12, QFont.Bold))
        # КОТОРМО: Материал
        p.drawText(20, 30, f"Материал: {self.material_name}")
        p.drawText(20, 50, f"ρ = {self.rho} Ом·мм²/м")


# --- ГЛАВНЫЙ КЛАСС ЛАБОРАТОРНОЙ ---
class ResistanceLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            # КОТОРМО: 8 Класс: Сопротивление проводника -> 8-класс: Өткөргүчтүн каршылыгы
            title="8-класс: Өткөргүчтүн каршылыгы",
            formula="R = ρ · L / S",
            description=(
                # КОТОРМО: Цель -> Максаты, Инструкция
                "<b>Максаты:</b> Каршылыктын узундуктан, жоондуктан жана материалдан көз карандылыгын изилдөө.<br>"
                "<b>Белгилөөлөр:</b><br>"
                "• <b>ρ (ро)</b> — салыштырма каршылык (материалга жараша).<br>"
                "• <b>L</b> — өткөргүчтүн узундугу (м).<br>"
                "• <b>S</b> — туура кесилиш аянты (мм²).<br><br>"
                "Материалды тандап, өлчөмдөрдү өзгөртүп, R маанисин эсептеңиз."
            )
        )
        # Данные материалов: rho в Ом*мм^2/м
        # КОТОРМО: Материалдардын аттары
        self.materials = {
            "Жез (Медь)": {"rho": 0.017, "color": QColor("#B87333"), "name": "Жез"},
            "Алюминий": {"rho": 0.028, "color": QColor("#D3D3D3"), "name": "Алюминий"},
            "Темир (Железо)": {"rho": 0.10, "color": QColor("#434B4D"), "name": "Темир"},
            "Нихром": {"rho": 1.10, "color": QColor("#A0A0A0"), "name": "Нихром"},
            "Күмүш (Серебро)": {"rho": 0.016, "color": QColor("#E0E0E0"), "name": "Күмүш"}
        }
        self.setup_inputs()

    def create_visualizer(self):
        return WireVisualizer()

    def setup_inputs(self):
        # Материал
        # КОТОРМО: Материал
        self.inputs_layout.addWidget(QLabel("Материал:"))
        self.combo_mat = QComboBox()
        self.combo_mat.addItems(self.materials.keys())
        self.combo_mat.currentTextChanged.connect(self.update_simulation)
        self.inputs_layout.addWidget(self.combo_mat)
        
        # Длина L
        # КОТОРМО: Узундук L (м)
        self.inputs_layout.addWidget(QLabel("Узундук L (м):"))
        self.slider_L = QSlider(Qt.Horizontal)
        self.slider_L.setRange(1, 100) # 0.1м до 10.0м
        self.slider_L.setValue(50)
        self.slider_L.valueChanged.connect(self.update_label_L)
        self.inputs_layout.addWidget(self.slider_L)
        
        self.label_L = QLabel("5.0 м")
        self.label_L.setAlignment(Qt.AlignCenter)
        self.inputs_layout.addWidget(self.label_L)
        
        # Площадь S
        # КОТОРМО: Аянт S (мм²)
        self.inputs_layout.addWidget(QLabel("Аянт S (мм²):"))
        self.slider_S = QSlider(Qt.Horizontal)
        self.slider_S.setRange(1, 50) # 0.1 мм2 до 5.0 мм2
        self.slider_S.setValue(10)
        self.slider_S.valueChanged.connect(self.update_label_S)
        self.inputs_layout.addWidget(self.slider_S)
        
        self.label_S = QLabel("1.0 мм²")
        self.label_S.setAlignment(Qt.AlignCenter)
        self.inputs_layout.addWidget(self.label_S)
        
        self.update_simulation()

    def update_label_L(self):
        val = self.slider_L.value() / 10.0
        self.label_L.setText(f"{val} м")
        self.update_simulation()

    def update_label_S(self):
        val = self.slider_S.value() / 10.0
        self.label_S.setText(f"{val} мм²")
        self.update_simulation()

    def update_simulation(self):
        mat_name = self.combo_mat.currentText()
        L = self.slider_L.value() / 10.0
        S = self.slider_S.value() / 10.0
        
        self.visualizer.update_params(L, S, self.materials[mat_name])

    def get_true_value(self):
        mat_name = self.combo_mat.currentText()
        rho = self.materials[mat_name]["rho"]
        L = self.slider_L.value() / 10.0
        S = self.slider_S.value() / 10.0
        
        # R = rho * L / S
        return rho * L / S

    def get_params_str(self):
        mat = self.combo_mat.currentText()
        L = self.slider_L.value() / 10.0
        S = self.slider_S.value() / 10.0
        return f"{mat}, L={L}м, S={S}мм²"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ResistanceLab()
    window.show()
    sys.exit(app.exec())