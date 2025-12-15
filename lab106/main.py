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
        
        self.inputs_group = QGroupBox("Параметры опыта")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        ctrl_layout.addWidget(self.inputs_group)
        
        ans_box = QGroupBox("Результат")
        ans_layout = QVBoxLayout(ans_box)
        ans_layout.addWidget(QLabel("Запишите макс. ЭДС (В):"))
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Пиковое значение")
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
        self.table.setHorizontalHeaderLabels(["Скорость v", "Число витков N", "Ваш ЭДС", "Статус"])
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
            QMessageBox.warning(self, "Ошибка", "Введите числовое значение.")
            return
            
        true_val = self.get_true_value()
        # Допуск 5%
        is_correct = abs(user_val - true_val) <= (0.05 * true_val if true_val != 0 else 0.1)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(self.get_params_str()))
        self.table.setItem(row, 1, QTableWidgetItem(f"{user_val:.2f}"))
        
        status_item = QTableWidgetItem("✅ Верно" if is_correct else "❌ Ошибка")
        status_item.setForeground(QBrush(QColor("green") if is_correct else QColor("red")))
        self.table.setItem(row, 3, status_item)
        
        if is_correct:
            QMessageBox.information(self, "Успех", f"Верно! ЭДС пропорциональна скорости.\nМаксимум был: {true_val:.2f} В")
        else:
            QMessageBox.warning(self, "Ошибка", f"Неверно.\nПравильный ответ: {true_val:.2f} В")


# --- ВИЗУАЛИЗАТОР ИНДУКЦИИ ---
class InductionVisualizer(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #333; border: 1px solid #555;")
        
        self.speed = 1.0 # м/с (условно)
        self.N_turns = 50
        
        # Состояние магнита
        self.magnet_x = -150 # Начальная позиция (слева)
        self.is_moving = False
        
        # Показания приборов
        self.current_emf = 0.0
        self.max_emf_detected = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(20) # 50 FPS для плавности

    def update_params(self, v, n):
        self.speed = v
        self.N_turns = n
        
    def start_experiment(self):
        self.magnet_x = -200
        self.is_moving = True
        self.max_emf_detected = 0.0

    def animate(self):
        if not self.is_moving:
            # Плавный возврат стрелки к нулю
            self.current_emf *= 0.9
            self.update()
            return

        # Двигаем магнит
        step = self.speed * 5 # Коэффициент скорости для анимации
        self.magnet_x += step
        
        # Расчет ЭДС
        # Модель: Магнитный поток Ф(x) похож на колокол (Гауссиана)
        # Ф(x) = B * S * exp(-x^2 / w^2)
        # E = -N * dФ/dt = -N * dФ/dx * dx/dt = -N * Ф'(x) * v
        # Ф'(x) ~ -2x * exp(...)
        
        # Центр катушки в x=0 (визуально центр экрана)
        # magnet_x - это координата центра магнита относительно центра катушки
        # Визуально центр экрана w/2. Пусть это будет x=0 в физике.
        
        # Переводим экранные координаты в физические (условные)
        # Пусть ширина катушки ~100 пикселей. Эффективная зона +/- 100.
        phys_x = self.magnet_x / 60.0 
        
        # Производная Гауссианы: -2 * x * exp(-x^2)
        # E ~ N * v * (2 * x * exp(-x^2))
        
        raw_signal = 2 * phys_x * math.exp(-(phys_x**2))
        
        # Коэффициент масштабирования, чтобы получить красивые вольты
        scale_factor = 0.5 
        
        # E = - N * v * signal. (Минус по закону Фарадея, но для модуля неважно)
        emf = - self.N_turns * self.speed * raw_signal * scale_factor
        
        self.current_emf = emf
        
        # Запоминаем пик (по модулю)
        if abs(emf) > self.max_emf_detected:
            self.max_emf_detected = abs(emf)
            
        # Если улетел далеко вправо - стоп
        if self.magnet_x > 200:
            self.is_moving = False
            
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        
        # 1. Гальванометр (Большой, сверху)
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
        
        # Стрелка
        # Макс отклонение +/- 5 делений. Пусть 1 деление = 1 В (условно)
        angle_max = 45 # градусов
        deflection = (self.current_emf / 5.0) * angle_max
        deflection = max(-60, min(60, deflection)) # Ограничитель
        
        p.save()
        p.translate(cx, meter_y + 10) # Точка вращения чуть ниже шкалы
        p.rotate(deflection)
        p.setPen(QPen(Qt.red, 3))
        p.drawLine(0, 0, 0, -80)
        p.restore()
        
        # Цифровое значение (для удобства)
        p.setPen(Qt.black)
        p.setFont(QFont("Arial", 12, QFont.Bold))
        p.drawText(cx + 110, meter_y - 30, f"{self.current_emf:.2f} В")
        
        # 2. Катушка (Соленоид)
        coil_w = 120
        coil_h = 80
        coil_x = cx - coil_w // 2
        coil_y = cy
        
        # Рисуем заднюю часть витков (темнее)
        p.setPen(QPen(QColor(139, 69, 19), 3)) # Медный цвет
        turns = 8
        step_x = coil_w / turns
        
        for i in range(turns):
            bx = coil_x + i * step_x
            # Полудуга сзади
            p.drawArc(int(bx), int(coil_y - coil_h/2), int(step_x), int(coil_h), 90*16, 180*16)

        # 3. Магнит (движется)
        mag_w = 100
        mag_h = 40
        # magnet_x - это смещение относительно центра
        mx = cx + self.magnet_x - mag_w // 2
        my = cy - mag_h // 2
        
        # Северный полюс (Синий)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("blue"))
        p.drawRect(int(mx), int(my), mag_w//2, mag_h)
        p.setPen(Qt.white)
        p.drawText(int(mx)+10, int(my)+25, "N")
        
        # Южный полюс (Красный)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("red"))
        p.drawRect(int(mx + mag_w//2), int(my), mag_w//2, mag_h)
        p.setPen(Qt.white)
        p.drawText(int(mx + mag_w//2)+10, int(my)+25, "S")
        
        # 4. Катушка (Передняя часть витков - поверх магнита)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(205, 127, 50), 3)) # Светлая медь
        for i in range(turns):
            bx = coil_x + i * step_x
            # Полудуга спереди
            p.drawArc(int(bx), int(coil_y - coil_h/2), int(step_x), int(coil_h), 270*16, 180*16)

        # Провода к гальванометру
        p.setPen(QPen(Qt.black, 2))
        p.drawLine(int(coil_x), int(coil_y - coil_h/2 + 10), int(cx - 80), int(meter_y + 20))
        p.drawLine(int(coil_x + coil_w), int(coil_y - coil_h/2 + 10), int(cx + 80), int(meter_y + 20))


# --- ГЛАВНЫЙ КЛАСС ЛАБОРАТОРНОЙ ---
class InductionLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            title="10 Класс: Электромагнитная индукция",
            formula="E = -N · ΔΦ/Δt ~ v",
            description=(
                "<b>Цель:</b> Исследовать зависимость ЭДС индукции от скорости изменения магнитного потока.<br>"
                "1. Установите скорость движения магнита (v) и число витков (N).<br>"
                "2. Нажмите <b>'Запустить магнит'</b>.<br>"
                "3. Следите за гальванометром. Стрелка отклонится сначала в одну сторону (вход), потом в другую (выход).<br>"
                "4. Запишите максимальное показание (по модулю)."
            )
        )
        self.setup_inputs()

    def create_visualizer(self):
        return InductionVisualizer()

    def setup_inputs(self):
        # Скорость
        self.inputs_layout.addWidget(QLabel("Скорость магнита v (м/с):"))
        self.slider_v = QSlider(Qt.Horizontal)
        self.slider_v.setRange(1, 10) # 0.1 до 1.0 м/с (условно)
        self.slider_v.setValue(5)
        self.inputs_layout.addWidget(self.slider_v)
        
        self.lbl_v = QLabel("0.5 м/с")
        self.lbl_v.setAlignment(Qt.AlignCenter)
        self.inputs_layout.addWidget(self.lbl_v)
        
        # Число витков
        self.inputs_layout.addWidget(QLabel("Число витков N:"))
        self.spin_n = QDoubleSpinBox()
        self.spin_n.setRange(10, 100)
        self.spin_n.setValue(50)
        self.spin_n.setSingleStep(10)
        self.inputs_layout.addWidget(self.spin_n)
        
        # Кнопка пуска
        self.btn_run = QPushButton("🧲 Запустить магнит")
        self.btn_run.setStyleSheet("font-size: 14px; padding: 8px; background-color: #DDDDFF;")
        self.btn_run.clicked.connect(self.run_experiment)
        self.inputs_layout.addWidget(self.btn_run)
        
        self.slider_v.valueChanged.connect(self.update_ui_labels)
        self.update_ui_labels()

    def update_ui_labels(self):
        v = self.slider_v.value() / 10.0
        self.lbl_v.setText(f"{v} м/с")
        # Обновляем параметры визуализатора (на лету)
        self.visualizer.update_params(v, self.spin_n.value())

    def run_experiment(self):
        v = self.slider_v.value() / 10.0
        self.visualizer.update_params(v, self.spin_n.value())
        self.visualizer.start_experiment()

    def get_true_value(self):
        # E_max ~ N * v * const
        # В нашем визуализаторе формула: emf = N * v * (2*x*exp...) * 0.5
        # Максимум функции x*exp(-x^2) равен 1/sqrt(2e) ≈ 0.4288 при x = 1/sqrt(2)
        # Итоговая формула в коде: scale_factor * 2 * 0.4288 = 0.5 * 0.8576 ≈ 0.4288
        # True E_max = N * v * 0.4288
        
        v = self.slider_v.value() / 10.0
        n = self.spin_n.value()
        
        # Вычисленный теоретический максимум для модели
        peak_factor = 0.42888 
        return n * v * peak_factor

    def get_params_str(self):
        v = self.slider_v.value() / 10.0
        return f"v={v} м/с, N={self.spin_n.value()}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = InductionLab()
    window.show()
    sys.exit(app.exec())