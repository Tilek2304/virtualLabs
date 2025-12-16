import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer, QPointF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Маятник + Секундомер
# ==========================================
class PendulumWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 450)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")
        
        # Ички параметрлер (Окуучуга көрүнбөйт)
        self.length = 1.0   
        self.g = 9.81       
        
        # Анимация өзгөрмөлөрү
        self.angle = 0.0    
        self.max_angle = math.radians(15)
        self.time = 0.0     
        self.is_running = False
        
        self.stopwatch_time = 0.0
        self.stopwatch_running = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(20) # 50 FPS (20ms)

    def set_physics(self, l, g):
        self.length = l
        self.g = g
        self.reset()

    def reset(self):
        self.time = 0.0
        self.angle = self.max_angle
        self.is_running = False
        self.stopwatch_time = 0.0
        self.stopwatch_running = False
        self.update()

    def start_swing(self):
        self.is_running = True

    def toggle_stopwatch(self):
        self.stopwatch_running = not self.stopwatch_running

    def reset_stopwatch(self):
        self.stopwatch_time = 0.0
        self.stopwatch_running = False
        self.update()

    def animate(self):
        # Маятник (Реалдуу убакыт)
        if self.is_running:
            self.time += 0.02
            # T = 2*pi*sqrt(l/g) -> omega = 2*pi/T = sqrt(g/l)
            omega = math.sqrt(self.g / self.length)
            self.angle = self.max_angle * math.cos(omega * self.time)
            
        # Секундомер
        if self.stopwatch_running:
            self.stopwatch_time += 0.02
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, 50

        # 1. Штатив
        painter.setPen(QPen(Qt.black, 3))
        painter.drawLine(cx - 50, cy, cx + 50, cy)
        
        # 2. Жип жана Жүк
        # Масштаб: Эгер жип узун болсо, экранга баткыдай кылабыз
        scale = 250 
        l_px = self.length * scale
        if l_px > h - 100: l_px = h - 100 # Чектөө
        
        bx = cx + l_px * math.sin(self.angle)
        by = cy + l_px * math.cos(self.angle)
        
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(cx, cy, bx, by)
        
        painter.setBrush(QColor(200, 50, 50))
        painter.setPen(Qt.black)
        painter.drawEllipse(QPointF(bx, by), 15, 15)

        # 3. Секундомер
        sw_x = w - 130
        sw_y = 80
        painter.setBrush(QColor(40, 40, 40))
        painter.setPen(Qt.black)
        painter.drawRect(sw_x, sw_y, 110, 50)
        
        painter.setPen(QColor(0, 255, 0)) # Жашыл сандар
        painter.setFont(QFont("Courier", 22, QFont.Bold))
        painter.drawText(sw_x + 10, sw_y + 35, f"{self.stopwatch_time:.2f}")
        
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 10))
        painter.drawText(sw_x, sw_y - 5, "Секундомер")

# ==========================================
# НЕГИЗГИ ТЕРЕЗЕ
# ==========================================
class LabFrequencyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш: Термелүү жыштыгын аныктоо")
        self.resize(1000, 600)
        
        self.true_freq = 0.0
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СОЛ ЖАК ---
        left_group = QGroupBox("Стенд")
        left_layout = QVBoxLayout()
        self.pendulum = PendulumWidget()
        left_layout.addWidget(self.pendulum)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- ОҢ ЖАК ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Инструкция
        task_g = QGroupBox("Тапшырма")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. 'Термелтүү' баскычын басыңыз."))
        task_l.addWidget(QLabel("2. Секундомерди иштетип, туура 10 термелүүнү санаңыз."))
        task_l.addWidget(QLabel("3. Убакытты (t) жазып, жыштыкты табыңыз."))
        task_l.addWidget(QLabel("Формула: ν = N / t (Жыштык = Саны / Убакыт)"))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Куралдар
        ctrl_g = QGroupBox("Куралдар")
        ctrl_l = QVBoxLayout()
        
        btn_swing = QPushButton("1. Термелтүү")
        btn_swing.clicked.connect(self.pendulum.start_swing)
        
        self.btn_timer = QPushButton("2. Секундомер (Старт/Стоп)")
        self.btn_timer.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.btn_timer.clicked.connect(self.toggle_timer_text)
        
        btn_reset_timer = QPushButton("Секундомерди нөлдөө")
        btn_reset_timer.clicked.connect(self.pendulum.reset_stopwatch)
        
        ctrl_l.addWidget(btn_swing)
        ctrl_l.addWidget(self.btn_timer)
        ctrl_l.addWidget(btn_reset_timer)
        ctrl_g.setLayout(ctrl_l)
        right_panel.addWidget(ctrl_g)

        # 3. Эсептөө
        calc_g = QGroupBox("Эсептөөлөр")
        calc_l = QVBoxLayout()
        
        self.in_t = QLineEdit(); self.in_t.setPlaceholderText("Убакыт t (с)")
        self.in_freq = QLineEdit(); self.in_freq.setPlaceholderText("Жыштык ν (Гц)")
        
        calc_l.addWidget(QLabel("10 термелүү убактысы (t):"))
        calc_l.addWidget(self.in_t)
        calc_l.addWidget(QLabel("Термелүү жыштыгы (ν = 10/t):"))
        calc_l.addWidget(self.in_freq)
        
        btn_check = QPushButton("Текшерүү")
        btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_check.clicked.connect(self.check_answer)
        
        btn_new = QPushButton("Жаңы эксперимент")
        btn_new.clicked.connect(self.new_experiment)
        
        calc_l.addWidget(btn_check)
        calc_l.addWidget(btn_new)
        
        calc_g.setLayout(calc_l)
        right_panel.addWidget(calc_g)
        
        right_panel.addStretch(1)

    def toggle_timer_text(self):
        self.pendulum.toggle_stopwatch()
        if self.pendulum.stopwatch_running:
            self.btn_timer.setText("ТОКТОТУУ")
            self.btn_timer.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        else:
            self.btn_timer.setText("БАШТОО")
            self.btn_timer.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

    def new_experiment(self):
        # ЭМИ БУЛ ЖЕРДЕ G ДАГЫ, L ДАГЫ РАНДОМ!
        # Бизге G белгилүү болушу шарт эмес, биз жыштыкты өлчөйбүз.
        # Бул Ай, Марс же Юпитер болушу мүмкүн.
        
        l = random.uniform(0.5, 1.5) # Узундук (м)
        g = random.uniform(3.0, 20.0) # Тартылуу күчү (м/с2) - РАНДОМ
        
        self.pendulum.set_physics(l, g)
        
        # Чыныгы жыштыкты эсептеп алабыз (Текшерүү үчүн)
        # T = 2*pi*sqrt(l/g)
        # Freq = 1/T = (1 / 2*pi) * sqrt(g/l)
        true_T = 2 * math.pi * math.sqrt(l / g)
        self.true_freq = 1.0 / true_T
        
        self.in_t.clear(); self.in_freq.clear()
        self.pendulum.reset_stopwatch()
        self.btn_timer.setText("2. Секундомер (Старт/Стоп)")
        self.btn_timer.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        
        QMessageBox.information(self, "Жаңы", "Жаңы шарттар түзүлдү (Башка планета болушу мүмкүн).\nМаятникти термелтип, жыштыгын өлчөңүз.")

    def check_answer(self):
        try:
            val = float(self.in_freq.text())
        except:
            QMessageBox.warning(self, "Ката", "Сан жазыңыз!")
            return
            
        # Каталык чеги: Секундомерди кол менен басканда реакция убактысы бар.
        # Мисалы: 10 термелүү 20сек болсо, адам 19.5 же 20.5 басышы мүмкүн.
        # Бул болжол менен 5-7% каталык.
        error_percent = abs(val - self.true_freq) / self.true_freq * 100
        
        if error_percent < 8.0:
            QMessageBox.information(self, "Туура", f"✅ Азаматсыз! Сиздин жыштык: {val:.3f} Гц\n(Чыныгы маани: {self.true_freq:.3f} Гц)")
        else:
            QMessageBox.warning(self, "Ката", f"❌ Туура эмес.\nСиздин жооп: {val:.3f} Гц\nЧыныгы маани: {self.true_freq:.3f} Гц\n\nСекундомерди тагыраак иштетиңиз.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabFrequencyApp()
    win.show()
    sys.exit(app.exec())