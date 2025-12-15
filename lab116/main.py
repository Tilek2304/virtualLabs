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
        
        self.inputs_group = QGroupBox("Источник излучения")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        ctrl_layout.addWidget(self.inputs_group)
        
        ans_box = QGroupBox("Измерение")
        ans_layout = QVBoxLayout(ans_box)
        ans_layout.addWidget(QLabel("Длина волны яркой линии (нм):"))
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Наведите курсор на линию")
        ans_layout.addWidget(self.answer_input)
        
        self.btn_check = QPushButton("Проверить ответ")
        self.btn_check.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.btn_check.clicked.connect(self.check_answer)
        ans_layout.addWidget(self.btn_check)
        ctrl_layout.addWidget(ans_box); ctrl_layout.addStretch()
        
        # Правая панель
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel)
        self.visualizer = self.create_visualizer()
        right_layout.addWidget(self.visualizer, stretch=1)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Газ", "Ваш ответ", "Эталон", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.table, stretch=0) # Таблица поменьше
        
        main_layout.addWidget(control_panel); main_layout.addWidget(right_panel)

    def create_visualizer(self): return QFrame()
    def get_true_value(self): return 0.0
    def get_params_str(self): return ""
    def setup_inputs(self): pass

    def check_answer(self):
        try:
            val = float(self.answer_input.text())
        except:
            QMessageBox.warning(self, "Ошибка", "Введите числовое значение (например, 587)."); return
            
        true_vals = self.get_true_value()
        
        # Погрешность +/- 3 нм (достаточно строго, так как есть точный курсор)
        hit = False
        target_line = 0
        
        if not true_vals: # Солнце
             hit = 400 <= val <= 750
             target_line = val
        else:
            # Ищем ближайшую правильную линию
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
        
        status = QTableWidgetItem("✅ Верно" if hit else "❌")
        status.setForeground(QBrush(QColor("green") if hit else QColor("red")))
        self.table.setItem(row, 3, status)
        
        if hit: QMessageBox.information(self, "Верно", f"Отлично! Линия {target_line} нм определена верно.")
        else: QMessageBox.warning(self, "Неверно", f"Вы промахнулись. Ближайшая линия была: {target_line} нм")


# --- УЛУЧШЕННЫЙ ВИЗУАЛИЗАТОР СПЕКТРА ---
class SpectraVisualizer(QFrame):
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True) # Включаем отслеживание мыши без клика
        self.setStyleSheet("background-color: black; border: 2px solid #555;")
        self.current_gas = "Водород"
        self.cursor_nm = None # Текущее положение курсора в нм
        
        # Данные спектров (Длина волны нм, Цвет HEX, Интенсивность 0.5-3.0 для ширины)
        self.spectra_data = {
            "Водород": [
                (656, "#FF0000", 2.5), # H-alpha
                (486, "#00FFFF", 1.5), # H-beta
                (434, "#0000FF", 1.0), # H-gamma
                (410, "#800080", 0.8)  # H-delta
            ],
            "Гелий": [
                (706, "#AA0000", 1.0),
                (667, "#FF0000", 1.5),
                (587, "#FFFF00", 3.0), # Желтая D3
                (501, "#00FF00", 1.2),
                (492, "#00E0E0", 1.0),
                (471, "#0000FF", 0.8),
                (447, "#000080", 1.5)
            ],
            "Неон": [
                # Неон - лес красных линий
                (640, "#FF0000", 2.0), (633, "#FF2000", 1.8), (614, "#FF4000", 1.5),
                (609, "#FF6000", 1.5), (594, "#FFAA00", 1.2), (585, "#FFFF00", 1.5),
                (540, "#00FF00", 0.5)
            ],
            "Ртуть": [
                (579, "#FFFF00", 1.8), # Дублет
                (577, "#FFFF00", 1.8),
                (546, "#00FF00", 3.0), # Зеленая
                (436, "#0000FF", 2.0), # Синяя
                (405, "#800080", 1.2)  # Фиолетовая
            ],
            "Непрерывный (Солнце)": [] 
        }

    def set_gas(self, gas_name):
        self.current_gas = gas_name
        self.update()

    def mouseMoveEvent(self, event):
        # Преобразование координаты X мыши в нанометры
        w = self.width()
        x = event.position().x()
        
        # Шкала от 380 до 750 нм
        min_nm = 380
        max_nm = 750
        
        # nm = min + (x / w) * (max - min)
        nm = min_nm + (x / w) * (max_nm - min_nm)
        
        # Ограничиваем диапазоном
        self.cursor_nm = max(min_nm, min(max_nm, nm))
        self.update()

    def leaveEvent(self, event):
        # Убираем курсор, когда мышь уходит с виджета
        self.cursor_nm = None
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        w = self.width()
        h = self.height()
        
        # Параметры шкалы
        min_nm = 380
        max_nm = 750
        range_nm = max_nm - min_nm
        scale_h = 60 # Высота области шкалы снизу
        
        # 1. Фон шкалы
        p.fillRect(0, h - scale_h, w, scale_h, QColor("#222"))
        p.setPen(QColor("#888"))
        p.drawLine(0, h - scale_h, w, h - scale_h) # Разделитель
        
        # 2. Отрисовка делений шкалы
        p.setFont(QFont("Arial", 8))
        
        # Шаг 10 нм
        for nm in range(380, 751, 10):
            x = ((nm - min_nm) / range_nm) * w
            
            if nm % 50 == 0:
                # Большое деление с цифрой
                p.setPen(QPen(Qt.white, 2))
                p.drawLine(int(x), h - scale_h, int(x), h - scale_h + 15)
                # Текст
                text_w = 30
                p.drawText(int(x) - text_w//2, h - 5, text_w, 20, Qt.AlignCenter, str(nm))
            else:
                # Малое деление
                p.setPen(QPen(Qt.gray, 1))
                p.drawLine(int(x), h - scale_h, int(x), h - scale_h + 8)

        # 3. Отрисовка спектральных линий
        spectrum_rect = QRectF(0, 0, w, h - scale_h)
        
        if self.current_gas == "Непрерывный (Солнце)":
            grad = QLinearGradient(0, 0, w, 0)
            # Цвета радуги по длинам волн (приблизительно)
            grad.setColorAt(0.0, QColor(80, 0, 150)) # 380
            grad.setColorAt(0.15, Qt.blue)           # 435
            grad.setColorAt(0.3, Qt.cyan)            # 490
            grad.setColorAt(0.45, Qt.green)          # 545
            grad.setColorAt(0.6, Qt.yellow)          # 600
            grad.setColorAt(0.75, QColor(255, 127, 0)) # 655
            grad.setColorAt(0.9, Qt.red)             # 710
            p.fillRect(spectrum_rect, grad)
        else:
            # Линейчатый спектр
            lines = self.spectra_data.get(self.current_gas, [])
            for nm, color_hex, intensity in lines:
                if nm < min_nm or nm > max_nm: continue
                
                x = ((nm - min_nm) / range_nm) * w
                
                c = QColor(color_hex)
                # Размытое свечение (glow)
                c.setAlpha(60)
                glow_width = 4 + int(intensity * 4)
                p.setPen(QPen(c, glow_width))
                p.drawLine(int(x), 0, int(x), int(h - scale_h))
                
                # Ядро линии
                c.setAlpha(255)
                core_width = 1 + int(intensity)
                p.setPen(QPen(c, core_width))
                p.drawLine(int(x), 0, int(x), int(h - scale_h))

        # 4. ИНТЕРАКТИВНЫЙ КУРСОР (ВИЗИР)
        if self.cursor_nm is not None:
            cx = ((self.cursor_nm - min_nm) / range_nm) * w
            
            # Вертикальная линия (белая пунктирная)
            p.setPen(QPen(QColor(255, 255, 255, 200), 1, Qt.DashLine))
            p.drawLine(int(cx), 0, int(cx), h)
            
            # Плашка с значением
            label_text = f"{self.cursor_nm:.1f} нм"
            p.setFont(QFont("Arial", 10, QFont.Bold))
            
            # Фон плашки
            text_rect_w = 70
            text_rect_h = 25
            
            # Позиционирование плашки, чтобы не вылезала за экран
            rx = cx + 10
            if rx + text_rect_w > w: rx = cx - 10 - text_rect_w
            ry = h/2
            
            p.setBrush(QColor(0, 0, 0, 180))
            p.setPen(QColor("#00FF00")) # Зеленая рамка
            p.drawRect(int(rx), int(ry), text_rect_w, text_rect_h)
            
            p.setPen(Qt.white)
            p.drawText(int(rx), int(ry), text_rect_w, text_rect_h, Qt.AlignCenter, label_text)


# --- ЛОГИКА ЛАБОРАТОРНОЙ ---
class SpectraLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            title="11 Класс: Изучение спектров",
            formula="Спектр излучения атомов линеен и уникален",
            description=(
                "<b>Инструкция:</b><br>"
                "1. Выберите газ из списка.<br>"
                "2. Наведите <b>курсор мыши</b> на яркую спектральную линию.<br>"
                "3. Считайте точное значение длины волны (появится рядом с курсором) и введите его в поле ответа.<br>"
                "Обратите внимание на желтую линию Гелия (D3) или зеленую линию Ртути."
            )
        )
        self.setup_inputs()

    def create_visualizer(self):
        return SpectraVisualizer()

    def setup_inputs(self):
        self.inputs_layout.addWidget(QLabel("Выберите газ:"))
        self.combo_gas = QComboBox()
        self.combo_gas.addItems(self.visualizer.spectra_data.keys())
        self.combo_gas.currentTextChanged.connect(self.update_gas)
        self.inputs_layout.addWidget(self.combo_gas)
        
        self.inputs_layout.addStretch()
        self.inputs_layout.addWidget(QLabel("<i>Подсказка: наведите курсор на цветную линию, чтобы увидеть точное значение.</i>"))

    def update_gas(self, text):
        self.visualizer.set_gas(text)

    def get_true_value(self):
        gas = self.combo_gas.currentText()
        if gas == "Непрерывный (Солнце)": return []
        
        lines = self.visualizer.spectra_data.get(gas, [])
        return [l[0] for l in lines] # Список правильных длин волн

    def get_params_str(self):
        return self.combo_gas.currentText()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = SpectraLab()
    window.show()
    sys.exit(app.exec())