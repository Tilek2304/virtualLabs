import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox,
    QSlider
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Жарыктын сынышы
# ==========================================
class RefractionWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 450)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")
        
        # Параметрлер
        self.n_glass = 1.5  # Айнектин сынуу көрсөткүчү
        self.n_air = 1.0
        self.angle_inc = 45.0 # Түшүү бурчу (градус)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def set_angle(self, angle):
        self.angle_inc = angle
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        # 1. Айнек пластина
        glass_w = 200
        glass_h = 100
        glass_rect = QRectF(cx - glass_w/2, cy, glass_w, glass_h)
        
        painter.setBrush(QColor(200, 230, 255, 150))
        painter.setPen(Qt.NoPen)
        painter.drawRect(glass_rect)
        
        # Чек ара сызыгы
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(cx - 150, cy, cx + 150, cy)
        
        # Нормаль (перпендикуляр)
        painter.setPen(QPen(Qt.black, 1, Qt.DashLine))
        painter.drawLine(cx, cy - 100, cx, cy + 100)

        # 2. Жарык нурлары (Жарыктын сынышы)
        alpha_rad = math.radians(self.angle_inc)
        len_ray = 150
        start_x = cx - len_ray * math.sin(alpha_rad)
        start_y = cy - len_ray * math.cos(alpha_rad)
        
        # Түшүүчү нур
        painter.setPen(QPen(Qt.red, 3))
        painter.drawLine(QPointF(start_x, start_y), QPointF(cx, cy))
        
        # Сынуучу нур
        # n1 * sin(a) = n2 * sin(b)
        sin_beta = (self.n_air / self.n_glass) * math.sin(alpha_rad)
        
        if abs(sin_beta) <= 1.0:
            beta_rad = math.asin(sin_beta)
            end_x = cx + len_ray * math.sin(beta_rad)
            end_y = cy + len_ray * math.cos(beta_rad)
            painter.setPen(QPen(Qt.blue, 3))
            painter.drawLine(QPointF(cx, cy), QPointF(end_x, end_y))
            
            # Бурчтарды жазуу
            painter.setPen(Qt.black)
            painter.setFont(QFont("Arial", 10))
            painter.drawText(cx - 30, cy - 20, f"α={self.angle_inc:.1f}°")
            beta_deg = math.degrees(beta_rad)
            painter.drawText(cx + 10, cy + 30, f"β={beta_deg:.1f}°")
        else:
            painter.drawText(cx, cy + 50, "Толук чагылуу!")

        # 3. Транспортир
        painter.setPen(QPen(QColor(100, 100, 100, 50), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(cx - 100, cy - 100, 200, 200, 0, 180*16)
        for i in range(0, 181, 10):
            ang = math.radians(i)
            p1 = QPointF(cx + 90*math.cos(ang), cy - 90*math.sin(ang))
            p2 = QPointF(cx + 100*math.cos(ang), cy - 100*math.sin(ang))
            painter.drawLine(p1, p2)

# ==========================================
# НЕГИЗГИ ТЕРЕЗЕ
# ==========================================
class LabRefractionApp(QWidget):
    def __init__(self):
        super().__init__()
        # ТЕМА ӨЗГӨРТҮЛДҮ
        self.setWindowTitle("Лабораториялык иш №20: Жарыктын сынышы")
        self.resize(1000, 600)
        
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СОЛ ЖАК ---
        left_group = QGroupBox("Стенд: Жарыктын сынышы")
        left_layout = QVBoxLayout()
        self.refraction = RefractionWidget()
        left_layout.addWidget(self.refraction)
        
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Түшүү бурчу (α):"))
        self.slider_alpha = QSlider(Qt.Horizontal)
        self.slider_alpha.setRange(0, 80)
        self.slider_alpha.setValue(45)
        self.slider_alpha.valueChanged.connect(self.update_angle)
        slider_layout.addWidget(self.slider_alpha)
        self.lbl_alpha = QLabel("45°")
        slider_layout.addWidget(self.lbl_alpha)
        
        left_layout.addLayout(slider_layout)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- ОҢ ЖАК ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Тапшырма
        task_g = QGroupBox("Тапшырма")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("Максат: Жарыктын сынышын изилдөө."))
        task_l.addWidget(QLabel("1. Түшүү бурчун (α) өзгөртүңүз."))
        task_l.addWidget(QLabel("2. Сынуу бурчун (β) аныктаңыз."))
        task_l.addWidget(QLabel("3. n = sin(α) / sin(β) формуласын текшериңиз."))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Эсептөө
        calc_g = QGroupBox("Эсептөө")
        calc_l = QVBoxLayout()
        
        self.in_alpha = QLineEdit(); self.in_alpha.setPlaceholderText("α (градус)")
        self.in_beta = QLineEdit(); self.in_beta.setPlaceholderText("β (градус)")
        self.in_n = QLineEdit(); self.in_n.setPlaceholderText("Сынуу көрсөткүчү (n)")
        
        calc_l.addWidget(QLabel("Түшүү бурчу α:"))
        calc_l.addWidget(self.in_alpha)
        calc_l.addWidget(QLabel("Сынуу бурчу β:"))
        calc_l.addWidget(self.in_beta)
        calc_l.addWidget(QLabel("Сиздин жооп (n):"))
        calc_l.addWidget(self.in_n)
        
        btn_check = QPushButton("Текшерүү")
        btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_check.clicked.connect(self.check_answer)
        
        btn_new = QPushButton("Жаңы чөйрө (Жаңы n)")
        btn_new.clicked.connect(self.new_experiment)
        
        calc_l.addWidget(btn_check)
        calc_l.addWidget(btn_new)
        
        calc_g.setLayout(calc_l)
        right_panel.addWidget(calc_g)
        right_panel.addStretch(1)

    def new_experiment(self):
        self.n_true = random.uniform(1.3, 1.8)
        self.refraction.n_glass = self.n_true
        self.in_alpha.clear(); self.in_beta.clear(); self.in_n.clear()
        QMessageBox.information(self, "Жаңы", "Жаңы чөйрө берилди. Жарыктын сынышын изилдеңиз.")

    def update_angle(self):
        val = self.slider_alpha.value()
        self.lbl_alpha.setText(f"{val}°")
        self.refraction.set_angle(val)
        self.in_alpha.setText(str(val))

    def check_answer(self):
        try:
            val = float(self.in_n.text())
        except:
            QMessageBox.warning(self, "Ката", "Сан жазыңыз!")
            return
            
        if abs(val - self.n_true) < 0.1:
            QMessageBox.information(self, "Туура", f"✅ Азаматсыз! n ≈ {self.n_true:.2f}")
        else:
            QMessageBox.warning(self, "Ката", f"❌ Туура эмес. n ≈ {self.n_true:.2f} болушу керек.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabRefractionApp()
    win.show()
    sys.exit(app.exec())