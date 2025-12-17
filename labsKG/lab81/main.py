import sys
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient
from PySide6.QtCore import Qt, QTimer, QRectF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Калориметр
# ==========================================
class CalorimeterWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 500)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")
        
        self.hot_vol = 0
        self.cold_vol = 0
        self.current_vol = 0
        self.target_vol = 0
        
        self.hot_temp = 0
        self.cold_temp = 0
        self.final_temp = 0
        self.current_temp = 20 # Бөлмө температурасы
        self.target_temp = 20
        
        self.is_mixed = False
        
        # Анимация
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def set_params(self, m1, t1, m2, t2):
        self.hot_vol = m1 # 1 г суу = 1 мл
        self.hot_temp = t1
        self.cold_vol = m2
        self.cold_temp = t2
        self.is_mixed = False
        
        # Баштапкы абал: Калориметр бош
        self.current_vol = 0
        self.target_vol = 0
        self.current_temp = 20
        self.target_temp = 20
        self.update()

    def pour_hot(self):
        self.target_vol = self.hot_vol
        self.target_temp = self.hot_temp
        self.is_mixed = False

    def pour_cold(self):
        self.target_vol = self.cold_vol
        self.target_temp = self.cold_temp
        self.is_mixed = False

    def mix_water(self):
        if self.hot_vol + self.cold_vol == 0: return
        self.target_vol = self.hot_vol + self.cold_vol
        # Жылуулук балансы: T = (m1*t1 + m2*t2) / (m1+m2)
        self.final_temp = (self.hot_vol*self.hot_temp + self.cold_vol*self.cold_temp) / self.target_vol
        self.target_temp = self.final_temp
        self.is_mixed = True

    def animate(self):
        # Көлөмдүн өзгөрүшү
        diff_v = self.target_vol - self.current_vol
        if abs(diff_v) > 0.5:
            self.current_vol += diff_v * 0.1
        else:
            self.current_vol = self.target_vol
            
        # Температуранын өзгөрүшү
        diff_t = self.target_temp - self.current_temp
        if abs(diff_t) > 0.1:
            self.current_temp += diff_t * 0.05
        else:
            self.current_temp = self.target_temp
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx = w // 2
        
        # 1. Калориметр (Идиш)
        cw = 200
        ch = 250
        cy = h - 50 - ch
        
        # Сырткы катмар (изолятор)
        painter.setBrush(QColor(200, 200, 200))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(cx - cw//2 - 10, cy, cw + 20, ch)
        
        # Ички идиш
        painter.setBrush(QColor(240, 240, 255))
        painter.drawRect(cx - cw//2, cy + 10, cw, ch - 20)
        
        # 2. Суу
        max_vol = 500 # Максималдуу сыйымдуулук
        if self.current_vol > 0:
            level_h = (self.current_vol / max_vol) * (ch - 40)
            if level_h > ch - 20: level_h = ch - 20
            
            # Суунун түсү температурага жараша (Көк -> Кызыл)
            # 0°C = Көк, 100°C = Кызыл
            r = int((self.current_temp / 100.0) * 255)
            b = 255 - r
            water_color = QColor(r, 50, b, 180)
            
            painter.setBrush(water_color)
            painter.setPen(Qt.NoPen)
            water_y = cy + ch - 10 - level_h
            painter.drawRect(cx - cw//2, water_y, cw, level_h)
            
            # Суунун бети
            painter.setPen(QPen(water_color.darker(), 2))
            painter.drawLine(cx - cw//2, water_y, cx + cw//2, water_y)

        # 3. Термометр
        th_x = cx + 60
        th_y = cy - 50
        th_h = 300
        th_w = 15
        
        # Корпус
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(th_x, th_y, th_w, th_h)
        painter.drawEllipse(th_x - 5, th_y + th_h - 10, 25, 25) # Шар
        
        # Сымап мамычасы
        mercury_h = (self.current_temp / 100.0) * (th_h - 20)
        painter.setBrush(QColor(255, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.drawRect(th_x + 5, th_y + th_h - 10 - mercury_h, 5, mercury_h + 10)
        painter.drawEllipse(th_x - 5, th_y + th_h - 10, 25, 25)
        
        # Температураны жазуу
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(th_x + 30, th_y + th_h - mercury_h, f"{self.current_temp:.1f}°C")

# ==========================================
# НЕГИЗГИ ТЕРЕЗЕ
# ==========================================
class LabMixApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш №10: Жылуулук балансы")
        self.resize(1000, 600)
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СОЛ ЖАК: Калориметр ---
        left_group = QGroupBox("Эксперимент")
        left_layout = QVBoxLayout()
        self.calorimeter = CalorimeterWidget()
        left_layout.addWidget(self.calorimeter)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- ОҢ ЖАК: Башкаруу ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Тапшырма
        task_g = QGroupBox("Тапшырма")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. Ысык жана муздак суунун параметрлерин караңыз."))
        task_l.addWidget(QLabel("2. Аларды калориметрге куюп аралаштырыңыз."))
        task_l.addWidget(QLabel("3. Акыркы температураны эсептеңиз."))
        task_l.addWidget(QLabel("Формула: T = (m1*t1 + m2*t2) / (m1+m2)"))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Параметрлер (Көрсөтүү гана)
        param_g = QGroupBox("Берилген маанилер")
        param_l = QVBoxLayout()
        self.lbl_hot = QLabel("Ысык суу: m1=... г, t1=... °C")
        self.lbl_cold = QLabel("Муздак суу: m2=... г, t2=... °C")
        
        param_l.addWidget(self.lbl_hot)
        param_l.addWidget(self.lbl_cold)
        param_g.setLayout(param_l)
        right_panel.addWidget(param_g)

        # 3. Баскычтар (Процесс)
        proc_g = QGroupBox("Процесс")
        proc_l = QVBoxLayout()
        
        btn_hot = QPushButton("Ысык сууну куюу")
        btn_hot.clicked.connect(self.calorimeter.pour_hot)
        
        btn_cold = QPushButton("Муздак сууну куюу")
        btn_cold.clicked.connect(self.calorimeter.pour_cold)
        
        btn_mix = QPushButton("Аралаштыруу")
        btn_mix.setStyleSheet("background-color: #2196F3; color: white;")
        btn_mix.clicked.connect(self.calorimeter.mix_water)
        
        proc_l.addWidget(btn_hot)
        proc_l.addWidget(btn_cold)
        proc_l.addWidget(btn_mix)
        proc_g.setLayout(proc_l)
        right_panel.addWidget(proc_g)

        # 4. Жооп
        ans_g = QGroupBox("Жооп")
        ans_l = QVBoxLayout()
        self.in_temp = QLineEdit()
        self.in_temp.setPlaceholderText("Температура T (°C)")
        
        btn_check = QPushButton("Текшерүү")
        btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_check.clicked.connect(self.check_answer)
        
        btn_new = QPushButton("Жаңы эксперимент")
        btn_new.clicked.connect(self.new_experiment)
        
        ans_l.addWidget(self.in_temp)
        ans_l.addWidget(btn_check)
        ans_l.addWidget(btn_new)
        ans_g.setLayout(ans_l)
        right_panel.addWidget(ans_g)
        
        right_panel.addStretch(1)

    def new_experiment(self):
        self.m1 = random.randint(50, 200)
        self.t1 = random.randint(60, 90)
        self.m2 = random.randint(50, 200)
        self.t2 = random.randint(10, 30)
        
        self.lbl_hot.setText(f"Ысык суу: m1={self.m1} г, t1={self.t1} °C")
        self.lbl_cold.setText(f"Муздак суу: m2={self.m2} г, t2={self.t2} °C")
        
        self.calorimeter.set_params(self.m1, self.t1, self.m2, self.t2)
        self.in_temp.clear()

    def check_answer(self):
        if not self.calorimeter.is_mixed:
            QMessageBox.warning(self, "Ката", "Адегенде сууну аралаштырыңыз!")
            return
            
        try:
            u_t = float(self.in_temp.text())
        except:
            QMessageBox.warning(self, "Ката", "Сан жазыңыз!")
            return
            
        real_t = self.calorimeter.final_temp
        
        if abs(u_t - real_t) < 0.5:
            QMessageBox.information(self, "Жыйынтык", f"✅ ТУУРА! T ≈ {real_t:.1f} °C")
        else:
            QMessageBox.warning(self, "Жыйынтык", f"❌ КАТА. Туура жооп: {real_t:.1f} °C")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabMixApp()
    win.show()
    sys.exit(app.exec())