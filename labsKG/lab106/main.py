import sys
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QFrame,
    QDoubleSpinBox, QMessageBox, QGroupBox, QHeaderView, QSlider
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygon
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
        
        # КОТОРМО: Параметры опыта -> Тажрыйбанын параметрлери
        self.inputs_group = QGroupBox("Тажрыйбанын параметрлери")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        ctrl_layout.addWidget(self.inputs_group)
        
        # КОТОРМО: Результат -> Жыйынтык
        ans_box = QGroupBox("Жыйынтык")
        ans_layout = QVBoxLayout(ans_box)
        # КОТОРМО: Запишите макс. ЭДС -> Максималдуу ЭККны жазыңыз (В)
        ans_layout.addWidget(QLabel("Максималдуу ЭККны жазыңыз (В):"))
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Пик мааниси")
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
        self.table.setHorizontalHeaderLabels(["Ылдамдык v", "Ороолор N", "Сиздин ЭКК", "Статус"])
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
        self.table.setItem(row, 2, QTableWidgetItem(f"{true_val:.2f}")) # КОТОРМО: Туура маани (жашыруун болсо да таблицада көрүнөт)
        
        # КОТОРМО: Верно/Ошибка -> Туура/Ката
        status_item = QTableWidgetItem("✅ Туура" if is_correct else "❌ Ката")
        status_item.setForeground(QBrush(QColor("green") if is_correct else QColor("red")))
        self.table.setItem(row, 3, status_item)
        
        if is_correct:
            # КОТОРМО: Успех -> Азаматсыз
            QMessageBox.information(self, "Азаматсыз", f"Туура! ЭКК ылдамдыкка түз пропорционалдуу.\nМаксимум болду: {true_val:.2f} В")
        else:
            # КОТОРМО: Ошибка -> Ката, Неверно -> Туура эмес
            QMessageBox.warning(self, "Ката", f"Туура эмес.\nТуура жооп: {true_val:.2f} В")


# --- ВИЗУАЛИЗАТОР ИНДУКЦИИ ---
class InductionVisualizer(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #333; border: 1px solid #555;")
        
        self.speed = 1.0 # м/с (шарттуу)
        self.N_turns = 50
        
        # Магниттин абалы
        self.magnet_x = -150 
        self.is_moving = False
        
        # Приборлордун көрсөткүчтөрү
        self.current_emf = 0.0
        self.max_emf_detected = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(20) # 50 FPS

    def update_params(self, v, n):
        self.speed = v
        self.N_turns = n
        
    def start_experiment(self):
        self.magnet_x = -200
        self.is_moving = True
        self.max_emf_detected = 0.0

    def animate(self):
        if not self.is_moving:
            # Жебенин жай кайтышы
            self.current_emf *= 0.9
            self.update()
            return

        # Магнитти жылдыруу
        step = self.speed * 5 
        self.magnet_x += step
        
        # ЭКК эсептөө
        phys_x = self.magnet_x / 60.0 
        
        # Гаусстун туундусу сыяктуу сигнал
        raw_signal = 2 * phys_x * math.exp(-(phys_x**2))
        
        scale_factor = 0.5 
        
        # E = - N * v * signal
        emf = - self.N_turns * self.speed * raw_signal * scale_factor
        
        self.current_emf = emf
        
        # Пикти эстеп калуу
        if abs(emf) > self.max_emf_detected:
            self.max_emf_detected = abs(emf)
            
        # Эгер оң жакка чыгып кетсе - токтотуу
        if self.magnet_x > 200:
            self.is_moving = False
            
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        
        # 1. Гальванометр (Чоң, үстүндө)
        meter_y = cy - 120
        p.setBrush(QColor(240, 240, 240))
        p.setPen(QPen(Qt.black, 3))
        p.drawRect(cx - 100, meter_y - 80, 200, 100)
        
        # Шкала
        p.setPen(QPen(Qt.black, 1))
        for i in range(-5, 6):
            x_tick = cx + i * 15
            h_tick = 10 if i == 0 else 5
            p.drawLine(int(x_tick), meter_y, int(x_tick), meter_y - h_tick)
        p.drawText(cx - 5, meter_y - 15, "0")
        
        # Жебе
        angle_max = 45 # градус
        deflection = (self.current_emf / 5.0) * angle_max
        deflection = max(-60, min(60, deflection)) 
        
        p.save()
        p.translate(cx, meter_y + 10) 
        p.rotate(deflection)
        p.setPen(QPen(Qt.red, 3))
        p.drawLine(0, 0, 0, -80)
        p.restore()
        
        # Сандык маани
        p.setPen(Qt.black)
        p.setFont(QFont("Arial", 12, QFont.Bold))
        # КОТОРМО: В
        p.drawText(cx + 110, meter_y - 30, f"{self.current_emf:.2f} В")
        
        # 2. Катушка (Соленоид)
        coil_w = 120
        coil_h = 80
        coil_x = cx - coil_w // 2
        coil_y = cy
        
        # Арткы ороолор
        p.setPen(QPen(QColor(139, 69, 19), 3)) # Жез түс
        turns = 8
        step_x = coil_w / turns
        
        for i in range(turns):
            bx = coil_x + i * step_x
            p.drawArc(int(bx), int(coil_y - coil_h/2), int(step_x), int(coil_h), 90*16, 180*16)

        # 3. Магнит
        mag_w = 100
        mag_h = 40
        mx = cx + self.magnet_x - mag_w // 2
        my = cy - mag_h // 2
        
        # Түндүк уюл (Көк)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("blue"))
        p.drawRect(int(mx), int(my), mag_w//2, mag_h)
        p.setPen(Qt.white)
        p.drawText(int(mx)+10, int(my)+25, "N")
        
        # Түштүк уюл (Кызыл)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("red"))
        p.drawRect(int(mx + mag_w//2), int(my), mag_w//2, mag_h)
        p.setPen(Qt.white)
        p.drawText(int(mx + mag_w//2)+10, int(my)+25, "S")
        
        # 4. Катушка (Алдыңкы ороолор)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(205, 127, 50), 3)) 
        for i in range(turns):
            bx = coil_x + i * step_x
            p.drawArc(int(bx), int(coil_y - coil_h/2), int(step_x), int(coil_h), 270*16, 180*16)

        # Зымдар
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(int(coil_x), int(coil_y - coil_h/2 + 10), int(cx - 80), int(meter_y + 20))
        p.drawLine(int(coil_x + coil_w), int(coil_y - coil_h/2 + 10), int(cx + 80), int(meter_y + 20))


# --- ГЛАВНЫЙ КЛАСС ЛАБОРАТОРНОЙ ---
class InductionLabSimple(BaseLabWindow):
    def __init__(self):
        super().__init__(
            # КОТОРМО: 10 Класс: Электромагнитная индукция -> 10-класс: Электромагниттик индукция
            title="10-класс: Электромагниттик индукция",
            formula="E = -N · ΔΦ/Δt ~ v",
            description=(
                # КОТОРМО: Цель -> Максаты, Инструкция
                "<b>Максаты:</b> Индукциялык ЭККнын магнит агымынын өзгөрүү ылдамдыгынан көз карандылыгын изилдөө.<br>"
                "1. Магниттин ылдамдыгын (v) жана ороолордун санын (N) орнотуңуз.<br>"
                "2. <b>'Магнитти жылдыруу'</b> баскычын басыңыз.<br>"
                "3. Гальванометрди байкаңыз. Жебе адегенде бир жакка, анан экинчи жакка кыйшаят.<br>"
                "4. Максималдуу маанини (модулу боюнча) жазыңыз."
            )
        )
        self.setup_inputs()

    def create_visualizer(self):
        return InductionVisualizer()

    def setup_inputs(self):
        # КОТОРМО: Скорость магнита -> Магниттин ылдамдыгы v (м/с)
        self.inputs_layout.addWidget(QLabel("Магниттин ылдамдыгы v (м/с):"))
        self.slider_v = QSlider(Qt.Horizontal)
        self.slider_v.setRange(1, 10) 
        self.slider_v.setValue(5)
        self.inputs_layout.addWidget(self.slider_v)
        
        self.lbl_v = QLabel("0.5 м/с")
        self.lbl_v.setAlignment(Qt.AlignCenter)
        self.inputs_layout.addWidget(self.lbl_v)
        
        # КОТОРМО: Число витков -> Ороолордун саны N
        self.inputs_layout.addWidget(QLabel("Ороолордун саны N:"))
        self.spin_n = QDoubleSpinBox()
        self.spin_n.setRange(10, 100)
        self.spin_n.setValue(50)
        self.spin_n.setSingleStep(10)
        self.inputs_layout.addWidget(self.spin_n)
        
        # КОТОРМО: Запустить магнит -> Магнитти жылдыруу
        self.btn_run = QPushButton("🧲 Магнитти жылдыруу")
        self.btn_run.setStyleSheet("font-size: 14px; padding: 8px; background-color: #DDDDFF;")
        self.btn_run.clicked.connect(self.run_experiment)
        self.inputs_layout.addWidget(self.btn_run)
        
        self.slider_v.valueChanged.connect(self.update_ui_labels)
        self.update_ui_labels()

    def update_ui_labels(self):
        v = self.slider_v.value() / 10.0
        self.lbl_v.setText(f"{v} м/с")
        self.visualizer.update_params(v, self.spin_n.value())

    def run_experiment(self):
        v = self.slider_v.value() / 10.0
        self.visualizer.update_params(v, self.spin_n.value())
        self.visualizer.start_experiment()

    def get_true_value(self):
        v = self.slider_v.value() / 10.0
        n = self.spin_n.value()
        
        # Теориялык коэффициент
        peak_factor = 0.42888 
        return n * v * peak_factor

    def get_params_str(self):
        v = self.slider_v.value() / 10.0
        return f"v={v} м/с, N={self.spin_n.value()}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = InductionLabSimple()
    window.show()
    sys.exit(app.exec())