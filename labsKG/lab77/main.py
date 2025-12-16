import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSlider, QTextEdit
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF

# ... (ExperimentWidget классы өзгөрүүсүз калат) ...
# Мен коддун көлөмүн азайтуу үчүн ExperimentWidget классын бул жерге кайталабайм, 
# ал мурункудай эле кала берет. Төмөндө толук код берилди.

class ExperimentWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(350, 500) # Өлчөмүн бир аз кичирейттим, тыкан болуш үчүн
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")

        self.px_per_cm = 10.0
        self.g = 9.81
        self.rho_water = 1000.0 

        self.body_mass = 0.2    
        self.body_vol = 0.0001  
        
        self.lift_h = 0.0       
        self.water_level_base = 250 
        self.current_force = 0.0

    def set_experiment(self, mass_kg, vol_m3):
        self.body_mass = mass_kg
        self.body_vol = vol_m3
        self.lift_h = 0.0
        self.update()

    def set_lift(self, value):
        self.lift_h = value / 100.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx = w // 2 

        # 1. СТЕНД (Штатив) - бийиктиги терезеге жараша өзгөрөт
        stand_top_y = 20
        stand_base_y = h - 20
        
        painter.setPen(QPen(QColor(80, 80, 80), 4))
        painter.drawLine(cx, stand_top_y, cx, stand_base_y) # Вертикал
        painter.drawLine(cx - 80, stand_base_y, cx + 80, stand_base_y) # Түбү
        
        # Кронштейн (Динамометр илинген жер) - жогору жакта туруктуу
        bracket_y = stand_top_y + 40
        painter.drawLine(cx, bracket_y, cx + 70, bracket_y) 

        # 2. МЕНЗУРКА - Стенддин түбүндө турат
        beaker_w = 120
        beaker_h = 180
        beaker_x = cx + 10
        # Мензурканы стенддин түбүнө жайгаштырабыз
        beaker_y = stand_base_y - beaker_h - 10 
        
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QColor(240, 248, 255, 100))
        painter.drawRect(beaker_x, beaker_y, beaker_w, beaker_h)
        
        # 3. ЖҮКТҮН ПОЗИЦИЯСЫН ЭСЕПТӨӨ
        # Динамометрдин илгичинин позициясы (Кронштейндин учу)
        hook_x = cx + 70
        hook_y = bracket_y
        
        # Динамометрдин узундугу
        dyn_h = 60
        dyn_y_pos = hook_y + 20 # Илгичтен бир аз төмөн
        
        # Жүктүн жибинин башталышы (Динамометрдин асты)
        string_start_y = dyn_y_pos + dyn_h
        
        # Жүктүн бийиктиги
        body_h = 50
        
        # Эми максималдуу түшүү аралыгын эсептейбиз:
        # Жүк мензурканын түбүнө чейин жетиши керек.
        # Мензурканын түбү = beaker_y + beaker_h
        # Жүктүн түбү ошол жерге жетиши үчүн:
        max_string_len = (beaker_y + beaker_h - body_h - 5) - string_start_y
        
        # Минималдуу жип (жогоруда турганда) - мензурканын үстүнөн бир аз жогору
        min_string_len = (beaker_y - body_h - 20) - string_start_y
        if min_string_len < 20: min_string_len = 20 # Өтө кыска болуп калбашы үчүн
        
        # Слайдерге жараша азыркы жиптин узундугу
        current_string_len = min_string_len + self.lift_h * (max_string_len - min_string_len)
        
        body_y = string_start_y + current_string_len
        body_x = hook_x
        body_r = 25

        # 4. СУУ ДЕҢГЭЭЛИ
        # Суунун бети (мензурканын ортосунда)
        water_surface_base_y = beaker_y + beaker_h / 2 + 20
        
        # Жүк сууга канчалык кирди?
        body_bottom_y = body_y + body_h
        
        # Чөмүлгөн бөлүгү (пиксель менен)
        submerged_px = max(0, body_bottom_y - water_surface_base_y)
        submerged_px = min(submerged_px, body_h) # Жүктүн бийиктигинен ашпайт
        
        submerged_ratio = submerged_px / body_h
        
        # Суунун деңгээлинин көтөрүлүшү
        water_rise = submerged_ratio * 15 
        current_water_y = water_surface_base_y - water_rise
        
        # Сууну тартуу
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 150, 255, 150))
        # Суу мензурканын түбүнөн баштап current_water_y чейин
        painter.drawRect(beaker_x + 2, int(current_water_y), beaker_w - 4, int(beaker_y + beaker_h - current_water_y - 2))
        
        # Шкала
        painter.setPen(QPen(Qt.black, 1))
        for i in range(1, 8):
            y_mark = beaker_y + beaker_h - i * 20
            painter.drawLine(beaker_x, int(y_mark), beaker_x + 8, int(y_mark))

        # 5. НЕРСЕНИ ТАРТУУ
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QColor(150, 100, 50)) 
        painter.drawRect(int(body_x - body_r), int(body_y), int(body_r*2), int(body_h))
        
        # Жип
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(int(hook_x), int(string_start_y), int(hook_x), int(body_y)) 

        # 6. ДИНАМОМЕТРДИ ТАРТУУ
        dyn_w = 36
        dyn_x = hook_x - dyn_w/2
        
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QColor(220, 220, 220))
        painter.drawRect(int(dyn_x), int(dyn_y_pos), int(dyn_w), int(dyn_h))
        
        # Күчтү эсептөө
        buoyant_force = self.rho_water * self.g * (self.body_vol * submerged_ratio)
        gravity_force = self.body_mass * self.g
        self.current_force = max(0, gravity_force - buoyant_force)
        
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(int(dyn_x), int(dyn_y_pos), int(dyn_w), int(dyn_h), Qt.AlignCenter, f"{self.current_force:.2f}")
        
        # Илгич
        painter.drawLine(int(hook_x), int(hook_y), int(hook_x), int(dyn_y_pos))

class LabArchimedesApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш №7: Архимед мыйзамы")
        self.resize(1000, 650)
        
        self.true_vol_ml = 0
        self.true_mass_g = 0
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СОЛ ЖАК: Стенд + Слайдер ---
        # Бул жерде горизонталдык жайгашуу: [Стенд] [Слайдер]
        left_group = QGroupBox("Тажрыйба стенди")
        left_layout = QHBoxLayout() # Horizontal!
        
        # 1. Стенд
        self.experiment = ExperimentWidget()
        left_layout.addWidget(self.experiment, 1) # Көбүрөөк орун алат
        
        # 2. Слайдер (Вертикалдуу башкаруу)
        slider_container = QWidget()
        slider_vbox = QVBoxLayout(slider_container)
        slider_vbox.setContentsMargins(0, 20, 0, 20)
        
        lbl_up = QLabel("Жогору")
        lbl_up.setAlignment(Qt.AlignCenter)
        
        self.slider = QSlider(Qt.Vertical)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)
        self.slider.setInvertedAppearance(True) # 0 үстүндө, 100 астында
        self.slider.valueChanged.connect(self.experiment.set_lift)
        
        lbl_down = QLabel("Төмөн")
        lbl_down.setAlignment(Qt.AlignCenter)
        
        slider_vbox.addWidget(lbl_up)
        slider_vbox.addWidget(self.slider, 1) # Слайдер созулат
        slider_vbox.addWidget(lbl_down)
        
        left_layout.addWidget(slider_container, 0) # Аз орун алат
        
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 4) # Сол жак чоңураак (4 бөлүк)

        # --- ОҢ ЖАК: Башкаруу ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 3) # Оң жак кичирээк (3 бөлүк)

        # 1. Тапшырма
        task_g = QGroupBox("Тапшырма")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. Жүктү абада өлчөңүз (P0)."))
        task_l.addWidget(QLabel("2. Слайдер менен жүктү сууга толук түшүрүңүз."))
        task_l.addWidget(QLabel("3. Жүктү сууда өлчөңүз (P1)."))
        task_l.addWidget(QLabel("4. Архимед күчүн табыңыз: Fa = P0 - P1."))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Киргизүү
        inp_g = QGroupBox("Маалыматтарды киргизүү")
        inp_l = QVBoxLayout()
        
        self.in_p0 = QLineEdit(); self.in_p0.setPlaceholderText("Салмак абада P0 (Н)")
        self.in_p1 = QLineEdit(); self.in_p1.setPlaceholderText("Салмак сууда P1 (Н)")
        self.in_fa = QLineEdit(); self.in_fa.setPlaceholderText("Архимед күчү Fa (Н)")
        # self.in_v  = QLineEdit(); self.in_v.setPlaceholderText("Көлөм V (мл)")
        
        inp_l.addWidget(QLabel("Салмак абада (P0):"))
        inp_l.addWidget(self.in_p0)
        inp_l.addWidget(QLabel("Салмак сууда (P1):"))
        inp_l.addWidget(self.in_p1)
        inp_l.addWidget(QLabel("Архимед күчү (Fa):"))
        inp_l.addWidget(self.in_fa)
        # inp_l.addWidget(QLabel("Нерсенин көлөмү (V):"))
        # inp_l.addWidget(self.in_v)
        
        inp_g.setLayout(inp_l)
        right_panel.addWidget(inp_g)

        # 3. Баскычтар
        btn_check = QPushButton("Текшерүү")
        btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_check.clicked.connect(self.check_answer)
        
        btn_new = QPushButton("Жаңы эксперимент")
        btn_new.clicked.connect(self.new_experiment)
        
        right_panel.addWidget(btn_check)
        right_panel.addWidget(btn_new)

        # 4. Журнал
        res_g = QGroupBox("Журнал")
        res_l = QVBoxLayout()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        res_l.addWidget(self.log)
        res_g.setLayout(res_l)
        right_panel.addWidget(res_g)

    def new_experiment(self):
        self.true_mass_g = random.randint(100, 300) 
        density = random.uniform(2.5, 8.0) 
        self.true_vol_ml = int(self.true_mass_g / density)
        
        mass_kg = self.true_mass_g / 1000.0
        vol_m3 = self.true_vol_ml * 1e-6
        self.experiment.set_experiment(mass_kg, vol_m3)
        
        self.slider.setValue(0)
        self.in_p0.clear()
        self.in_p1.clear()
        self.in_fa.clear()
        # self.in_v.clear()
        self.log.append("--- Жаңы тапшырма берилди ---")

    def check_answer(self):
        try:
            u_p0 = float(self.in_p0.text())
            u_p1 = float(self.in_p1.text())
            u_fa = float(self.in_fa.text())
            # u_v  = float(self.in_v.text())
        except:
            QMessageBox.warning(self, "Ката", "Сандарды туура киргизиңиз!")
            return

        g = 9.81
        true_p0 = (self.true_mass_g / 1000.0) * g
        true_fa = 1000.0 * g * (self.true_vol_ml * 1e-6)
        true_p1 = true_p0 - true_fa
        
        is_p0 = abs(u_p0 - true_p0) < 0.1
        is_p1 = abs(u_p1 - true_p1) < 0.1
        is_fa = abs(u_fa - true_fa) < 0.1
        # is_v  = abs(u_v - self.true_vol_ml) < 5.0
        
        if is_p0 and is_p1 and is_fa:
            self.log.append(f"<span style='color:green'>✅ <b>ТУУРА!</b> (Fa={true_fa:.2f}H)</span>")
            # if is_v:
            #     self.log.append(f"   Көлөм туура: {self.true_vol_ml} мл")
            # else:
            #     self.log.append(f"   Көлөм ката. V = Fa / (ρ*g).")
        else:
            self.log.append(f"<span style='color:red'>❌ <b>КАТА.</b> Кайра текшериңиз.</span>")
            self.log.append(f"   P0 ≈ {true_p0:.2f}, P1 ≈ {true_p1:.2f}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabArchimedesApp()
    win.show()
    sys.exit(app.exec())