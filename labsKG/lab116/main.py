import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QFrame,
    QDoubleSpinBox, QMessageBox, QGroupBox, QHeaderView, QComboBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QCursor
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF

# --- БАЗОВЫЙ ШАБЛОН ---
class BaseLabWindow(QWidget):
    def __init__(self, title, formula, description):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(1100, 600)
        
        main_layout = QHBoxLayout(self)
        
        # Левая панель
        control_panel = QFrame(); control_panel.setFixedWidth(320)
        control_panel.setStyleSheet("background-color: #f5f5f5; border-right: 1px solid #ddd;")
        ctrl_layout = QVBoxLayout(control_panel)
        
        ctrl_layout.addWidget(QLabel(f"<h2>{title}</h2>"))
        desc_lbl = QLabel(description); desc_lbl.setWordWrap(True); ctrl_layout.addWidget(desc_lbl)
        ctrl_layout.addWidget(QLabel("<hr>"))
        
        # КОТОРМО: Источник излучения -> Нурлануу булагы
        self.inputs_group = QGroupBox("Нурлануу булагы")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        ctrl_layout.addWidget(self.inputs_group)
        
        # КОТОРМО: Измерение -> Өлчөө
        ans_box = QGroupBox("Өлчөө")
        ans_layout = QVBoxLayout(ans_box)
        # КОТОРМО: Длина волны... -> Жарык сызыктын толкун узундугу (нм):
        ans_layout.addWidget(QLabel("Жарык сызыктын толкун узундугу (нм):"))
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Курсорду сызыкка алып барыңыз")
        ans_layout.addWidget(self.answer_input)
        
        # КОТОРМО: Проверить ответ -> Жоопту текшерүү
        self.btn_check = QPushButton("Жоопту текшерүү")
        self.btn_check.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.btn_check.clicked.connect(self.check_answer)
        ans_layout.addWidget(self.btn_check)
        ctrl_layout.addWidget(ans_box); ctrl_layout.addStretch()
        
        # Правая панель
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel)
        self.visualizer = self.create_visualizer()
        right_layout.addWidget(self.visualizer, stretch=1)
        
        self.table = QTableWidget(0, 4)
        # КОТОРМО: Заголовки таблицы
        self.table.setHorizontalHeaderLabels(["Газ", "Сиздин жооп", "Туура жооп", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.table, stretch=0)
        
        main_layout.addWidget(control_panel); main_layout.addWidget(right_panel)

    def create_visualizer(self): return QFrame()
    def get_true_value(self): return 0.0
    def get_params_str(self): return ""
    def setup_inputs(self): pass

    def check_answer(self):
        try:
            val = float(self.answer_input.text())
        except:
            QMessageBox.warning(self, "Ката", "Сан маанисин киргизиңиз (мисалы, 587)."); return
            
        true_vals = self.get_true_value()
        
        # Погрешность +/- 3 нм
        hit = False
        target_line = 0
        
        if not true_vals: # Күн
             hit = 400 <= val <= 750
             target_line = val
        else:
            closest_diff = 1000
            for line in true_vals:
                diff = abs(val - line)
                if diff < closest_diff:
                    closest_diff = diff
                    target_line = line
            
            if closest_diff <= 3.0:
                hit = True

        row = self.table.rowCount(); self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(self.get_params_str()))
        self.table.setItem(row, 1, QTableWidgetItem(f"{val:.1f}"))
        
        true_str = str(int(target_line)) if true_vals else "400-750"
        self.table.setItem(row, 2, QTableWidgetItem(true_str))
        
        status = QTableWidgetItem("✅ Туура" if hit else "❌")
        status.setForeground(QBrush(QColor("green") if hit else QColor("red")))
        self.table.setItem(row, 3, status)
        
        if hit: QMessageBox.information(self, "Азаматсыз", f"Эң сонун! {target_line} нм сызыгы туура аныкталды.")
        else: QMessageBox.warning(self, "Ката", f"Туура эмес. Эң жакын сызык: {target_line} нм")


# --- УЛУЧШЕННЫЙ ВИЗУАЛИЗАТОР СПЕКТРА ---
class SpectraVisualizer(QFrame):
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True) 
        self.setStyleSheet("background-color: black; border: 2px solid #555;")
        self.current_gas = "Водород" # Демейки: Суутек
        self.cursor_nm = None 
        
        # Данные спектров (Толкун узундугу, Түс HEX, Интенсивдүүлүк)
        self.spectra_data = {
            "Суутек (Водород)": [
                (656, "#FF0000", 2.5), # H-alpha
                (486, "#00FFFF", 1.5), # H-beta
                (434, "#0000FF", 1.0), # H-gamma
                (410, "#800080", 0.8)  # H-delta
            ],
            "Гелий": [
                (706, "#AA0000", 1.0),
                (667, "#FF0000", 1.5),
                (587, "#FFFF00", 3.0), # Сары D3
                (501, "#00FF00", 1.2),
                (492, "#00E0E0", 1.0),
                (471, "#0000FF", 0.8),
                (447, "#000080", 1.5)
            ],
            "Неон": [
                (640, "#FF0000", 2.0), (633, "#FF2000", 1.8), (614, "#FF4000", 1.5),
                (609, "#FF6000", 1.5), (594, "#FFAA00", 1.2), (585, "#FFFF00", 1.5),
                (540, "#00FF00", 0.5)
            ],
            "Сымап (Ртуть)": [
                (579, "#FFFF00", 1.8), 
                (577, "#FFFF00", 1.8),
                (546, "#00FF00", 3.0), # Жашыл
                (436, "#0000FF", 2.0), # Көк
                (405, "#800080", 1.2)  # Кызгылт көк
            ],
            "Үзгүлтүксүз (Күн)": [] 
        }

    def set_gas(self, gas_name):
        self.current_gas = gas_name
        self.update()

    def mouseMoveEvent(self, event):
        w = self.width()
        x = event.position().x()
        
        min_nm = 380
        max_nm = 750
        
        nm = min_nm + (x / w) * (max_nm - min_nm)
        self.cursor_nm = max(min_nm, min(max_nm, nm))
        self.update()

    def leaveEvent(self, event):
        self.cursor_nm = None
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        w = self.width()
        h = self.height()
        
        min_nm = 380
        max_nm = 750
        range_nm = max_nm - min_nm
        scale_h = 60 
        
        # 1. Фон шкалы
        p.fillRect(0, h - scale_h, w, scale_h, QColor("#222"))
        p.setPen(QColor("#888"))
        p.drawLine(0, h - scale_h, w, h - scale_h) 
        
        # 2. Шкаланын бөлүнүштөрү
        p.setFont(QFont("Arial", 8))
        
        for nm in range(380, 751, 10):
            x = ((nm - min_nm) / range_nm) * w
            
            if nm % 50 == 0:
                p.setPen(QPen(Qt.white, 2))
                p.drawLine(int(x), h - scale_h, int(x), h - scale_h + 15)
                text_w = 30
                p.drawText(int(x) - text_w//2, h - 5, text_w, 20, Qt.AlignCenter, str(nm))
            else:
                p.setPen(QPen(Qt.gray, 1))
                p.drawLine(int(x), h - scale_h, int(x), h - scale_h + 8)

        # 3. Спектрдик сызыктар
        spectrum_rect = QRectF(0, 0, w, h - scale_h)
        
        if self.current_gas == "Үзгүлтүксүз (Күн)":
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0.0, QColor(80, 0, 150)) 
            grad.setColorAt(0.15, Qt.blue)           
            grad.setColorAt(0.3, Qt.cyan)            
            grad.setColorAt(0.45, Qt.green)          
            grad.setColorAt(0.6, Qt.yellow)          
            grad.setColorAt(0.75, QColor(255, 127, 0)) 
            grad.setColorAt(0.9, Qt.red)             
            p.fillRect(spectrum_rect, grad)
        else:
            lines = self.spectra_data.get(self.current_gas, [])
            for nm, color_hex, intensity in lines:
                if nm < min_nm or nm > max_nm: continue
                
                x = ((nm - min_nm) / range_nm) * w
                
                c = QColor(color_hex)
                c.setAlpha(60)
                glow_width = 4 + int(intensity * 4)
                p.setPen(QPen(c, glow_width))
                p.drawLine(int(x), 0, int(x), int(h - scale_h))
                
                c.setAlpha(255)
                core_width = 1 + int(intensity)
                p.setPen(QPen(c, core_width))
                p.drawLine(int(x), 0, int(x), int(h - scale_h))

        # 4. ИНТЕРАКТИВДҮҮ КУРСОР
        if self.cursor_nm is not None:
            cx = ((self.cursor_nm - min_nm) / range_nm) * w
            
            p.setPen(QPen(QColor(255, 255, 255, 200), 1, Qt.DashLine))
            p.drawLine(int(cx), 0, int(cx), h)
            
            label_text = f"{self.cursor_nm:.1f} нм"
            p.setFont(QFont("Arial", 10, QFont.Bold))
            
            text_rect_w = 70
            text_rect_h = 25
            
            rx = cx + 10
            if rx + text_rect_w > w: rx = cx - 10 - text_rect_w
            ry = h/2
            
            p.setBrush(QColor(0, 0, 0, 180))
            p.setPen(QColor("#00FF00")) 
            p.drawRect(int(rx), int(ry), text_rect_w, text_rect_h)
            
            p.setPen(Qt.white)
            p.drawText(int(rx), int(ry), text_rect_w, text_rect_h, Qt.AlignCenter, label_text)


# --- ЛОГИКА ЛАБОРАТОРНОЙ ---
class SpectraLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            # КОТОРМО: 11 Класс: Изучение спектров -> 11-класс: Спектрлерди үйрөнүү
            title="11-класс: Спектрлерди үйрөнүү",
            formula="Атомдордун нурлануу спектри сызыктуу жана уникалдуу",
            description=(
                # КОТОРМО: Инструкция...
                "<b>Көрсөтмө:</b><br>"
                "1. Тизмеден газды тандаңыз.<br>"
                "2. Жаркыраган спектрдик сызыкка <b>чычкандын курсорун</b> алып барыңыз.<br>"
                "3. Толкун узундугунун так маанисин (курсордун жанында чыгат) окуп, жооп талаасына жазыңыз.<br>"
                "Гелийдин сары сызыгына (D3) же Сымаптын жашыл сызыгына көңүл буруңуз."
            )
        )
        self.setup_inputs()

    def create_visualizer(self):
        return SpectraVisualizer()

    def setup_inputs(self):
        # КОТОРМО: Выберите газ -> Газды тандаңыз
        self.inputs_layout.addWidget(QLabel("Газды тандаңыз:"))
        self.combo_gas = QComboBox()
        self.combo_gas.addItems(self.visualizer.spectra_data.keys())
        self.combo_gas.currentTextChanged.connect(self.update_gas)
        self.inputs_layout.addWidget(self.combo_gas)
        
        self.inputs_layout.addStretch()
        # КОТОРМО: Подсказка...
        self.inputs_layout.addWidget(QLabel("<i>Кеңеш: так маанини көрүү үчүн курсорду түстүү сызыкка алып барыңыз.</i>"))

    def update_gas(self, text):
        self.visualizer.set_gas(text)

    def get_true_value(self):
        gas = self.combo_gas.currentText()
        if gas == "Үзгүлтүксүз (Күн)": return []
        
        lines = self.visualizer.spectra_data.get(gas, [])
        return [l[0] for l in lines] 

    def get_params_str(self):
        return self.combo_gas.currentText()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = SpectraLab()
    window.show()
    sys.exit(app.exec())