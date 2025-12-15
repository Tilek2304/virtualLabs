import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QFrame,
    QDoubleSpinBox, QMessageBox, QGroupBox, QHeaderView, QSlider
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QRadialGradient
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF

# --- КОНСТАНТЫ ---
C_LIGHT = 299792458       # м/с
E_CHARGE = 1.60218e-19    # Кл
H_PLANCK_TRUE = 6.626e-34 # Дж*с
WORK_FUNCTION_EV = 2.2    # Чыгуу жумушу (мисалы, Калий), эВ
WORK_FUNCTION_J = WORK_FUNCTION_EV * E_CHARGE

# --- БАЗОВЫЙ ШАБЛОН ---
class BaseLabWindow(QWidget):
    def __init__(self, title, formula, description):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(1100, 700)
        
        main_layout = QHBoxLayout(self)
        
        # Левая панель
        control_panel = QFrame(); control_panel.setFixedWidth(340)
        control_panel.setStyleSheet("background-color: #f5f5f5; border-right: 1px solid #ddd;")
        ctrl_layout = QVBoxLayout(control_panel)
        
        ctrl_layout.addWidget(QLabel(f"<h2>{title}</h2>"))
        formula_lbl = QLabel(f"<div style='background:#eef; padding:10px; border-radius:5px; font-size:16px; color:blue'><b>{formula}</b></div>")
        ctrl_layout.addWidget(formula_lbl)
        desc_lbl = QLabel(description); desc_lbl.setWordWrap(True); ctrl_layout.addWidget(desc_lbl)
        ctrl_layout.addWidget(QLabel("<hr>"))
        
        # КОТОРМО: Управление установкой -> Түзүлүштү башкаруу
        self.inputs_group = QGroupBox("Түзүлүштү башкаруу")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        ctrl_layout.addWidget(self.inputs_group)
        
        # КОТОРМО: Результат -> Жыйынтык
        ans_box = QGroupBox("Жыйынтык")
        ans_layout = QVBoxLayout(ans_box)
        # КОТОРМО: Рассчитайте h -> h маанисин эсептеңиз (Дж·с)
        ans_layout.addWidget(QLabel("h маанисин эсептеңиз (Дж·с):"))
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Мисалы: 6.63e-34")
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
        self.table.setHorizontalHeaderLabels(["λ (нм), U (В)", "Сиздин h", "Эталон", "Статус"])
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
            QMessageBox.warning(self, "Ката", "Сан киргизиңиз (мисалы, 6.6e-34 форматында).")
            return
            
        true_val = H_PLANCK_TRUE
        # Допуск 10%
        is_correct = abs(user_val - true_val) <= 0.1 * true_val
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(self.get_params_str()))
        self.table.setItem(row, 1, QTableWidgetItem(f"{user_val:.2e}"))
        self.table.setItem(row, 2, QTableWidgetItem(f"{true_val:.2e}"))
        
        # КОТОРМО: Верно/Ошибка -> Туура/Ката
        status_item = QTableWidgetItem("✅ Туура" if is_correct else "❌ Ката")
        status_item.setForeground(QBrush(QColor("green") if is_correct else QColor("red")))
        self.table.setItem(row, 3, status_item)
        
        if is_correct:
            # КОТОРМО: Успех -> Азаматсыз
            QMessageBox.information(self, "Азаматсыз", "Браво! Сиз фундаменталдык турактуулукту аныктадыңыз.")
        else:
            # КОТОРМО: Ошибка -> Ката, Неверно -> Туура эмес
            QMessageBox.warning(self, "Ката", f"Туура эмес.\nh ≈ {true_val:.3e}")


# --- ВИЗУАЛИЗАТОР ФОТОЭФФЕКТА ---
class PhotoEffectVisualizer(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #222; border: 1px solid #555;")
        
        self.wavelength_nm = 500.0 # нм
        self.voltage = 0.0         # В (терс - кармоочу)
        self.intensity = 50        # %
        
        # Физика
        self.electrons = [] # [x, y, vx, vy, color]
        self.photocurrent = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def update_params(self, nm, u, inten):
        self.wavelength_nm = nm
        self.voltage = u
        self.intensity = inten

    def nm_to_rgb(self, nm):
        # Толкун узундугунан түскө өтүү
        r, g, b = 0, 0, 0
        if 380 <= nm < 440:
            r = -(nm - 440) / (440 - 380); b = 1.0
        elif 440 <= nm < 490:
            g = (nm - 440) / (490 - 440); b = 1.0
        elif 490 <= nm < 510:
            g = 1.0; b = -(nm - 510) / (510 - 490)
        elif 510 <= nm < 580:
            r = (nm - 510) / (580 - 510); g = 1.0
        elif 580 <= nm < 645:
            r = 1.0; g = -(nm - 645) / (645 - 580)
        elif 645 <= nm <= 780:
            r = 1.0
        return QColor(int(r * 255), int(g * 255), int(b * 255))

    def animate(self):
        w = self.width()
        
        # 1. Фотондун энергиясы жана макс. кин. энергия
        # E_ph = h * c / lambda
        E_ph_J = (H_PLANCK_TRUE * C_LIGHT) / (self.wavelength_nm * 1e-9)
        E_k_max_J = E_ph_J - WORK_FUNCTION_J
        
        # 2. Электрондордун жаралышы
        # Эгер фотондун энергиясы чыгуу жумушунан чоң болсо
        if E_k_max_J > 0 and self.intensity > 0:
            # Ыктымалдуулук интенсивдүүлүккө пропорционалдуу
            if random.randint(0, 100) < (self.intensity / 5):
                # Баштапкы ылдамдык v = sqrt(2Ek/m).
                # Визуалдаштыруу үчүн масштабдайбыз
                v_scale = math.sqrt(E_k_max_J) * 2e9 
                # Электрондор ар кандай ылдамдыкка ээ (0дөн v_max чейин)
                v_real = v_scale * random.uniform(0.5, 1.0)
                
                self.electrons.append({
                    'x': 60, # Катоддо
                    'y': random.randint(100, 300),
                    'vx': v_real,
                    'vy': random.uniform(-1, 1)
                })

        # 3. Электрондордун кыймылы
        # Ылдамдануу a = F/m = (e * U / d) / m
        acc = self.voltage * 0.8 
        
        anode_x = w - 60
        reached_anode = 0
        
        survived_electrons = []
        for e in self.electrons:
            e['vx'] += acc # Ылдамдыкты өзгөртөбүз
            e['x'] += e['vx']
            e['y'] += e['vy']
            
            # Эгер артка кетсе (талаадан чагылышса)
            if e['vx'] < 0 and e['x'] < 60:
                continue # Катодго сиңди
            
            # Эгер анодго жетсе
            if e['x'] > anode_x:
                reached_anode += 1
                continue # Анодго сиңди (ток)
            
            # Эгер Y чегинен чыкса
            if not (50 < e['y'] < 350):
                continue
                
            survived_electrons.append(e)
            
        self.electrons = survived_electrons
        
        # Амперметрдин көрсөткүчүн жай өзгөртүү (сглаживание)
        target_current = reached_anode * 10 
        self.photocurrent = self.photocurrent * 0.9 + target_current * 0.1
        
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        # 1. Лампа жана Жарык
        light_color = self.nm_to_rgb(self.wavelength_nm)
        p.setPen(QPen(light_color, 2))
        
        # Нуралар
        opacity = int(self.intensity * 2.55)
        beam_color = QColor(light_color)
        beam_color.setAlpha(opacity)
        p.setBrush(QBrush(beam_color))
        p.setPen(Qt.NoPen)
        
        # Жарык конусу
        polygon = [QPointF(0, 0), QPointF(60, 80), QPointF(60, 320), QPointF(0, 400)]
        p.drawPolygon(polygon)
        
        # 2. Электроддор
        p.setBrush(Qt.gray)
        p.setPen(QPen(Qt.white, 2))
        
        # Катод (Сол)
        p.drawRect(50, 80, 10, 240)
        p.drawText(40, 70, "K")
        
        # Анод (Оң)
        anode_x = w - 60
        p.drawRect(anode_x, 80, 10, 240)
        p.drawText(anode_x, 70, "A")
        
        # 3. Электрондор
        p.setBrush(Qt.cyan)
        p.setPen(Qt.NoPen)
        for e in self.electrons:
            p.drawEllipse(QPointF(e['x'], e['y']), 3, 3)
            
        # 4. Амперметр (Ток)
        p.setPen(QPen(Qt.white, 2))
        p.setBrush(Qt.NoBrush)
        center_x = w // 2
        ammeter_y = h - 80
        p.drawEllipse(QPointF(center_x, ammeter_y), 40, 40)
        p.drawText(center_x - 5, ammeter_y + 5, "A")
        
        # Жебе
        angle = -45 + (self.photocurrent / 50.0) * 90 
        angle = max(-45, min(45, angle))
        
        p.save()
        p.translate(center_x, ammeter_y)
        p.rotate(angle)
        p.setPen(QPen(Qt.red, 3))
        p.drawLine(0, 0, 0, -30)
        p.restore()
        
        # Токтун мааниси
        p.setPen(Qt.white)
        p.setFont(QFont("Arial", 12))
        # КОТОРМО: мкА
        p.drawText(center_x - 30, ammeter_y + 60, f"I = {self.photocurrent:.1f} мкА")
        
        # Инфо
        p.setFont(QFont("Arial", 10))
        p.setPen(Qt.gray)
        # КОТОРМО: Работа выхода -> Чыгуу жумушу A
        p.drawText(10, h - 10, f"Чыгуу жумушу A = {WORK_FUNCTION_EV} эВ")


# --- ГЛАВНЫЙ КЛАСС ЛАБОРАТОРНОЙ ---
class PhotoEffectLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            # КОТОРМО: 10 Класс: Постоянная Планка -> 10-класс: Планк турактуулугу (Фотоэффект)
            title="10-класс: Планк турактуулугу (Фотоэффект)",
            formula="h = (e·U_кар + A) / ν",
            description=(
                # КОТОРМО: Цель -> Максаты, Инструкция
                "<b>Максаты:</b> Планк турактуулугун аныктоо.<br>"
                "1. Жарыктын толкун узундугун (λ) орнотуңуз.<br>"
                "2. Фототок пайда болушу үчүн интенсивдүүлүктү көбөйтүңүз.<br>"
                "3. Чыңалууну (терс жакка) азайтып отуруп, амперметрдин жебеси нөлгө түшкөн учурду кармаңыз. Бул <b>U_кар</b> (кармоочу чыңалуу).<br>"
                "4. U_кар, жыштык (ν = c/λ) жана чыгуу жумушу A (2.2 эВ) аркылуу h маанисин эсептеңиз."
            )
        )
        self.setup_inputs()

    def create_visualizer(self):
        return PhotoEffectVisualizer()

    def setup_inputs(self):
        # КОТОРМО: Длина волны -> Толкун узундугу λ (нм)
        self.inputs_layout.addWidget(QLabel("Толкун узундугу λ (нм):"))
        self.slider_lam = QSlider(Qt.Horizontal)
        self.slider_lam.setRange(300, 800) # УФ - ИК
        self.slider_lam.setValue(500)
        self.lbl_lam = QLabel("500 нм")
        self.lbl_lam.setAlignment(Qt.AlignCenter)
        self.inputs_layout.addWidget(self.slider_lam)
        self.inputs_layout.addWidget(self.lbl_lam)
        
        # КОТОРМО: Интенсивность -> Жарыктын интенсивдүүлүгү (%)
        self.inputs_layout.addWidget(QLabel("Жарыктын интенсивдүүлүгү (%):"))
        self.slider_int = QSlider(Qt.Horizontal)
        self.slider_int.setRange(0, 100)
        self.slider_int.setValue(50)
        self.inputs_layout.addWidget(self.slider_int)
        
        # КОТОРМО: Напряжение -> Чыңалуу U (В)
        self.inputs_layout.addWidget(QLabel("Чыңалуу U (В):"))
        self.spin_u = QDoubleSpinBox()
        self.spin_u.setRange(-5.0, 5.0)
        self.spin_u.setValue(0.0)
        self.spin_u.setSingleStep(0.1)
        self.spin_u.setSuffix(" В")
        self.inputs_layout.addWidget(self.spin_u)
        
        # Сигналдар
        self.slider_lam.valueChanged.connect(self.update_simulation)
        self.slider_int.valueChanged.connect(self.update_simulation)
        self.spin_u.valueChanged.connect(self.update_simulation)
        
        self.update_simulation()

    def update_simulation(self):
        nm = self.slider_lam.value()
        self.lbl_lam.setText(f"{nm} нм")
        
        inten = self.slider_int.value()
        u = self.spin_u.value()
        
        self.visualizer.update_params(nm, u, inten)

    def get_params_str(self):
        return f"λ={self.slider_lam.value()}нм, U={self.spin_u.value()}В"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PhotoEffectLab()
    window.show()
    sys.exit(app.exec())