import sys
import time
import math
import random
import json
from dataclasses import dataclass, asdict
from typing import List, Dict

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QFrame,
    QDoubleSpinBox, QSlider, QMessageBox, QTabWidget, QGroupBox, QFileDialog
)
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF

# --- КОНСТАНТЫ ---
G = 9.81
PI = 3.14159
H_PLANCK = 6.626e-34
E_CHARGE = 1.602e-19
C_LIGHT = 3e8

# --- МОДЕЛИ ДАННЫХ ---
@dataclass
class Measurement:
    timestamp: float
    params: Dict[str, float]  # Входные параметры (I, R, t...)
    results: Dict[str, float] # Вычисленные моделью значения
    user_answer: float        # Ответ ученика
    is_correct: bool

# --- БАЗОВЫЙ КЛАСС ВИЗУАЛИЗАЦИИ ---
class BaseVisualWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(500, 300)
        self.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.t = 0.0  # Время симуляции

    def start_animation(self):
        self.timer.start(30) # 30ms ~ 33 FPS

    def stop_animation(self):
        self.timer.stop()

    def animate(self):
        self.t += 0.05
        self.update()

# --- БАЗОВЫЙ КЛАСС ЛАБОРАТОРНОЙ (ШАБЛОН) ---
class BaseLabWindow(QWidget):
    def __init__(self, title, formula_html, description):
        super().__init__()
        self.setWindowTitle(f"Лабораторная: {title}")
        self.resize(1200, 800)
        self.measurements: List[Measurement] = []
        
        # Основной Layout
        main_layout = QHBoxLayout(self)

        # --- ЛЕВАЯ ПАНЕЛЬ (Управление) ---
        control_panel = QFrame()
        control_panel.setFixedWidth(350)
        self.control_layout = QVBoxLayout(control_panel)
        
        # Описание
        lbl_title = QLabel(f"<h3>{title}</h3>")
        lbl_formula = QLabel(f"<div style='font-size:14px; color:blue'>{formula_html}</div>")
        lbl_desc = QLabel(description)
        lbl_desc.setWordWrap(True)
        
        self.control_layout.addWidget(lbl_title)
        self.control_layout.addWidget(lbl_formula)
        self.control_layout.addWidget(lbl_desc)
        self.control_layout.addWidget(QLabel("<hr>"))

        # Место для контролов (добавляются в наследниках)
        self.inputs_group = QGroupBox("Параметры эксперимента")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        self.control_layout.addWidget(self.inputs_group)

        # Ввод ответа
        self.control_layout.addWidget(QLabel("<b>Ваш результат:</b>"))
        self.answer_input = QLineEdit()
        self.control_layout.addWidget(self.answer_input)

        # Кнопки
        btn_box = QHBoxLayout()
        self.btn_check = QPushButton("Проверить")
        self.btn_check.clicked.connect(self.check_answer)
        self.btn_check.setStyleSheet("background-color: #d4edda; padding: 8px;")
        
        self.btn_reset = QPushButton("Сброс")
        self.btn_reset.clicked.connect(self.reset_lab)
        
        btn_box.addWidget(self.btn_check)
        btn_box.addWidget(self.btn_reset)
        self.control_layout.addLayout(btn_box)
        
        self.control_layout.addStretch() # Пружина вниз

        # --- ПРАВАЯ ПАНЕЛЬ (Визуализация + Таблица) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Визуализация
        self.visualizer = self.create_visualizer() # Метод должен быть переопределен
        right_layout.addWidget(self.visualizer, stretch=2)

        # Таблица результатов
        self.table = QTableWidget(0, 4) # Default columns
        right_layout.addWidget(self.table, stretch=1)

        main_layout.addWidget(control_panel)
        main_layout.addWidget(right_panel)

        self.setup_inputs() # Метод для наследников
        self.visualizer.start_animation()

    # --- Методы для переопределения ---
    def create_visualizer(self):
        return BaseVisualWidget()

    def setup_inputs(self):
        pass

    def get_current_params(self):
        return {}

    def calculate_true_value(self, params):
        return 0.0

    # --- Общая логика ---
    def check_answer(self):
        try:
            user_val = float(self.answer_input.text().replace(',', '.'))
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите число")
            return

        params = self.get_current_params()
        true_val = self.calculate_true_value(params)
        
        # Допустимая погрешность 5%
        error = abs(user_val - true_val)
        is_correct = error <= 0.05 * abs(true_val) if true_val != 0 else error < 0.1

        # Сохранение
        meas = Measurement(time.time(), params, {"True": true_val}, user_val, is_correct)
        self.measurements.append(meas)
        self.update_table(meas)

        if is_correct:
            QMessageBox.information(self, "Верно!", f"Отличная работа.\nПравильный ответ: {true_val:.2f}")
        else:
            QMessageBox.warning(self, "Неверно", f"Попробуйте еще раз.\nПравильный ответ: {true_val:.2f}")

    def update_table(self, m: Measurement):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Формируем строку: Параметры | Ответ ученика | Эталон | Статус
        param_str = ", ".join([f"{k}={v:.1f}" for k,v in m.params.items()])
        
        self.table.setItem(row, 0, QTableWidgetItem(param_str))
        self.table.setItem(row, 1, QTableWidgetItem(str(m.user_answer)))
        self.table.setItem(row, 2, QTableWidgetItem(f"{list(m.results.values())[0]:.2f}"))
        
        status = QTableWidgetItem("✅" if m.is_correct else "❌")
        status.setBackground(QColor("#d4edda") if m.is_correct else QColor("#f8d7da"))
        self.table.setItem(row, 3, status)

    def reset_lab(self):
        self.measurements.clear()
        self.table.setRowCount(0)
        self.answer_input.clear()

# ============================================================================
# ЛАБОРАТОРНАЯ 1: ЗАКОН ДЖОУЛЯ-ЛЕНЦА (8 КЛАСС)
# ============================================================================

class JouleLenzVisualizer(BaseVisualWidget):
    def __init__(self):
        super().__init__()
        self.I = 0
        self.R = 0
        self.heat_color = 0 # 0 - blue, 255 - red
    
    def update_params(self, I, R):
        self.I = I
        self.R = R

    def animate(self):
        super().animate()
        # Имитация нагрева: чем больше ток и сопротивление, тем быстрее краснеет
        power = self.I**2 * self.R
        step = power * 0.05
        self.heat_color = min(255, self.heat_color + step)
        if self.I == 0: self.heat_color = max(0, self.heat_color - 2) # Остывание
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        # Рисуем стакан
        rect = QRectF(200, 100, 150, 180)
        water_color = QColor(int(self.heat_color), 0, 255 - int(self.heat_color), 150)
        p.setBrush(water_color)
        p.setPen(QPen(Qt.black, 3))
        p.drawRect(rect)
        
        # Спираль
        p.setPen(QPen(QColor(50, 50, 50), 4))
        path = QPointF(220, 100)
        for i in range(10):
            y = 100 + i * 15
            x = 220 if i % 2 == 0 else 330
            p.drawLine(QPointF(220, y), QPointF(330, y+15))
        
        # Пузырьки (если горячо)
        if self.heat_color > 100:
            p.setBrush(Qt.white)
            p.setPen(Qt.NoPen)
            for _ in range(5):
                rx = random.randint(210, 340)
                ry = random.randint(120, 260)
                p.drawEllipse(rx, ry, 5, 5)

class JouleLenzLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            "Закон Джоуля–Ленца", 
            "Q = I² · R · t",
            "Рассчитайте количество теплоты, выделившееся в проводнике."
        )
        self.table.setHorizontalHeaderLabels(["Параметры (I, R, t)", "Ваш Q (Дж)", "Эталон Q", "Статус"])
        self.answer_input.setPlaceholderText("Введите Q (Дж)")

    def create_visualizer(self):
        return JouleLenzVisualizer()

    def setup_inputs(self):
        self.spin_I = QDoubleSpinBox(); self.spin_I.setPrefix("I = "); self.spin_I.setSuffix(" А"); self.spin_I.setRange(0, 10)
        self.spin_R = QDoubleSpinBox(); self.spin_R.setPrefix("R = "); self.spin_R.setSuffix(" Ом"); self.spin_R.setRange(0, 100)
        self.spin_t = QDoubleSpinBox(); self.spin_t.setPrefix("t = "); self.spin_t.setSuffix(" с"); self.spin_t.setRange(0, 1000)
        
        self.inputs_layout.addWidget(self.spin_I)
        self.inputs_layout.addWidget(self.spin_R)
        self.inputs_layout.addWidget(self.spin_t)
        
        # Обновление анимации при изменении параметров
        self.spin_I.valueChanged.connect(self.update_vis)
        self.spin_R.valueChanged.connect(self.update_vis)

    def update_vis(self):
        self.visualizer.update_params(self.spin_I.value(), self.spin_R.value())

    def get_current_params(self):
        return {"I": self.spin_I.value(), "R": self.spin_R.value(), "t": self.spin_t.value()}

    def calculate_true_value(self, p):
        return (p["I"] ** 2) * p["R"] * p["t"]

# ============================================================================
# ЛАБОРАТОРНАЯ 2: ПРУЖИННЫЙ МАЯТНИК (9 КЛАСС)
# ============================================================================

class PendulumVisualizer(BaseVisualWidget):
    def __init__(self):
        super().__init__()
        self.mass = 1.0
        self.k = 10.0
        self.amplitude = 50.0 # пиксели

    def update_params(self, m, k):
        self.mass = m
        self.k = k

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        # Расчет смещения y = A * cos(omega * t)
        omega = math.sqrt(self.k / self.mass) if self.mass > 0 else 0
        dy = self.amplitude * math.cos(omega * self.t)
        
        center_x = self.width() // 2
        base_y = 50
        equilibrium_y = 200
        current_y = equilibrium_y + dy

        # Крепление
        p.fillRect(center_x - 50, base_y - 10, 100, 10, Qt.darkGray)

        # Пружина (рисуем зигзаг)
        p.setPen(QPen(Qt.black, 2))
        segments = 20
        spring_h = current_y - base_y
        seg_h = spring_h / segments
        prev_pt = QPointF(center_x, base_y)
        
        for i in range(1, segments + 1):
            offset = 15 if i % 2 else -15
            curr_pt = QPointF(center_x + offset, base_y + i * seg_h)
            p.drawLine(prev_pt, curr_pt)
            prev_pt = curr_pt
        
        p.drawLine(prev_pt, QPointF(center_x, current_y))

        # Груз
        radius = 20 + self.mass * 2 # Визуально зависит от массы
        p.setBrush(QColor("#e74c3c"))
        p.drawEllipse(QPointF(center_x, current_y + radius), radius, radius)
        
        p.drawText(10, 20, f"Время t: {self.t:.1f} с")

class SpringPendulumLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            "Пружинный маятник",
            "T = 2π √(m / k)",
            "Определите период колебаний маятника."
        )
        self.table.setHorizontalHeaderLabels(["Параметры (m, k)", "Ваш T (с)", "Эталон T", "Статус"])
        self.answer_input.setPlaceholderText("Введите Период T (с)")

    def create_visualizer(self):
        return PendulumVisualizer()

    def setup_inputs(self):
        self.spin_m = QDoubleSpinBox(); self.spin_m.setPrefix("m = "); self.spin_m.setSuffix(" кг"); self.spin_m.setRange(0.1, 10); self.spin_m.setValue(1)
        self.spin_k = QDoubleSpinBox(); self.spin_k.setPrefix("k = "); self.spin_k.setSuffix(" Н/м"); self.spin_k.setRange(1, 200); self.spin_k.setValue(20)
        
        self.inputs_layout.addWidget(self.spin_m)
        self.inputs_layout.addWidget(self.spin_k)
        
        self.spin_m.valueChanged.connect(self.update_vis)
        self.spin_k.valueChanged.connect(self.update_vis)
        self.update_vis()

    def update_vis(self):
        self.visualizer.update_params(self.spin_m.value(), self.spin_k.value())

    def get_current_params(self):
        return {"m": self.spin_m.value(), "k": self.spin_k.value()}

    def calculate_true_value(self, p):
        return 2 * PI * math.sqrt(p["m"] / p["k"])

# ============================================================================
# ЛАБОРАТОРНАЯ 3: ФОТОЭФФЕКТ (10-11 КЛАСС)
# ============================================================================

class PhotoEffectVisualizer(BaseVisualWidget):
    def __init__(self):
        super().__init__()
        self.intensity = 50
        self.voltage = 0.0 # Задерживающее напряжение (отрицательное)
        self.electrons = [] # List of [x, y, speed_x]

    def update_params(self, intensity, voltage):
        self.intensity = intensity
        self.voltage = voltage # U

    def animate(self):
        # Генерация электронов (вероятность зависит от интенсивности)
        if random.randint(0, 100) < self.intensity:
            # Начальная скорость зависит (условно) от энергии света, 
            # здесь упрощенно считаем что свет фиксированной частоты, 
            # но V0 зависит от задерживающего напряжения
            v_init = 5.0 
            self.electrons.append([50, random.randint(100, 200), v_init])

        # Движение электронов
        surviving = []
        for e in self.electrons:
            # Ускорение (торможение) a ~ U
            # Если U < 0 (задерживающее), электроны тормозят
            acc = self.voltage * 0.1 
            e[2] += acc # changing speed
            e[0] += e[2] # changing x position

            # Если скорость стала < 0, электрон летит назад
            if e[0] < 50: # Вернулся на катод
                continue 
            if e[0] > 400: # Долетел до анода
                continue # Ток пошел
            
            surviving.append(e)
        self.electrons = surviving
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), Qt.black)
        
        # Катод
        p.fillRect(40, 80, 10, 140, Qt.gray)
        p.setPen(Qt.white)
        p.drawText(30, 70, "Катод (-)")

        # Анод
        p.fillRect(400, 80, 10, 140, Qt.gray)
        p.drawText(390, 70, "Анод (+)")

        # Свет
        opacity = int(self.intensity * 2.5)
        p.setPen(QPen(QColor(255, 255, 0, opacity), 2))
        for i in range(5):
            p.drawLine(0, 100+i*20, 40, 120+i*10)

        # Электроны
        p.setBrush(Qt.cyan)
        p.setPen(Qt.NoPen)
        for e in self.electrons:
            p.drawEllipse(QPointF(e[0], e[1]), 3, 3)

class PhotoEffectLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            "Фотоэффект: Постоянная Планка",
            "h = e·U / ν",
            "Подберите запирающее напряжение U для данной частоты света, чтобы ток стал равен 0. Рассчитайте h."
        )
        self.table.setHorizontalHeaderLabels(["ν (Гц), U (В)", "Ваш h (Дж·с)", "Эталон", "Статус"])
        self.answer_input.setPlaceholderText("Введите h (например 6.63e-34)")

    def create_visualizer(self):
        return PhotoEffectVisualizer()

    def setup_inputs(self):
        self.slider_intensity = QSlider(Qt.Horizontal)
        self.slider_intensity.setRange(0, 100)
        self.slider_intensity.setValue(50)
        
        self.spin_freq = QDoubleSpinBox()
        self.spin_freq.setPrefix("ν = ")
        self.spin_freq.setSuffix(" x10^14 Гц")
        self.spin_freq.setRange(4.0, 10.0) # Видимый спектр
        self.spin_freq.setValue(5.0)

        self.spin_U = QDoubleSpinBox()
        self.spin_U.setPrefix("U задерж. = ")
        self.spin_U.setSuffix(" В")
        self.spin_U.setRange(-5.0, 0.0)
        self.spin_U.setSingleStep(0.1)
        self.spin_U.setValue(0)

        self.inputs_layout.addWidget(QLabel("Интенсивность света:"))
        self.inputs_layout.addWidget(self.slider_intensity)
        self.inputs_layout.addWidget(self.spin_freq)
        self.inputs_layout.addWidget(self.spin_U)

        self.slider_intensity.valueChanged.connect(self.update_vis)
        self.spin_U.valueChanged.connect(self.update_vis)
        self.spin_freq.valueChanged.connect(self.update_vis)

    def update_vis(self):
        # Логика: если e*U > Ek_max, электроны не долетают
        # Ek_max = h*nu - A_out
        # Пусть Работа выхода A = 2.0 эВ (примерно цезий)
        A_ev = 2.0
        A_j = A_ev * E_CHARGE
        
        nu = self.spin_freq.value() * 1e14
        Ek_max = (H_PLANCK * nu) - A_j
        
        # Если энергия фотона меньше работы выхода - фотоэффекта нет
        if Ek_max < 0: 
            intensity_factor = 0 
        else:
            intensity_factor = self.slider_intensity.value()

        # Реальное запирающее напряжение (U_stop должно быть отрицательным)
        # Ek_max = e * |U_stop|
        U_stop_needed = - (Ek_max / E_CHARGE) 
        
        current_U = self.spin_U.value()
        
        # Передаем в визуализатор "эффективное напряжение" для анимации скорости
        # Если current_U < U_stop_needed, электроны остановятся
        self.visualizer.update_params(intensity_factor, current_U)

    def get_current_params(self):
        return {"nu_10^14": self.spin_freq.value(), "U": self.spin_U.value()}

    def calculate_true_value(self, p):
        # h = e * U / nu (упрощенно, предполагая что студент нашел U запирающее)
        # В реальности студент вводит U, и мы проверяем формулу
        # Но здесь мы знаем входные данные. 
        # Давайте просто вернем константу Планка как эталон
        return H_PLANCK

# --- ГЛАВНОЕ ОКНО (МЕНЮ) ---
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Виртуальная Лаборатория по Физике")
        self.resize(400, 500)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Выберите лабораторную работу</h2>"))
        
        btn_8 = QPushButton("8 класс: Закон Джоуля-Ленца")
        btn_8.clicked.connect(lambda: self.open_lab(JouleLenzLab()))
        layout.addWidget(btn_8)

        btn_9 = QPushButton("9 класс: Пружинный маятник")
        btn_9.clicked.connect(lambda: self.open_lab(SpringPendulumLab()))
        layout.addWidget(btn_9)

        btn_10 = QPushButton("10-11 класс: Фотоэффект")
        btn_10.clicked.connect(lambda: self.open_lab(PhotoEffectLab()))
        layout.addWidget(btn_10)

        layout.addStretch()
        layout.addWidget(QLabel("© 2025 Physics Virtual Labs"))

    def open_lab(self, lab_window):
        self.lab = lab_window
        self.lab.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Стилизация (Dark/Light mode neutral)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())