import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer, QPointF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Бюретка + Тамчы + Тараза
# ==========================================
class SurfaceTensionWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 450)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")
        
        # Параметрлер
        self.sigma = 0.073  
        self.d = 0.002      
        self.g = 9.81
        
        # Абал
        self.drops_count = 0
        self.total_mass = 0.0 
        self.drop_radius = 0
        self.drop_y = 50
        
        self.is_dripping = False
        self.is_finished = False # Бүттүбү?
        
        # Анимация
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def toggle_dripping(self):
        if self.is_finished: return # Эгер 50 тамчы болсо, токтоп тура берет
        self.is_dripping = not self.is_dripping
        if self.is_dripping and self.drop_radius == 0:
            self.drop_radius = 2
            self.drop_y = 50

    def animate(self):
        if not self.is_dripping: return
        
        # Тамчынын өсүшү
        if self.drop_y == 50:
            if self.drop_radius < 8:
                self.drop_radius += 0.2
            else:
                self.drop_y += 5 # Үзүлдү
        else:
            # Түшүү
            self.drop_y += 10
            if self.drop_y > 300: # Стаканга түштү
                self.add_drop()
                # Жаңы тамчыга даярдоо
                if not self.is_finished:
                    self.drop_radius = 2
                    self.drop_y = 50
                else:
                    self.is_dripping = False
                    self.drop_radius = 0
                
        self.update()

    def add_drop(self):
        if self.is_finished: return

        self.drops_count += 1
        m_drop = (math.pi * self.d * self.sigma) / self.g
        m_drop *= random.uniform(0.98, 1.02)
        self.total_mass += m_drop
        
        # 50 тамчыдан кийин токтотуу
        if self.drops_count >= 50:
            self.is_finished = True
            self.is_dripping = False
            self.parent().parent().experiment_finished() # Callback

    def reset(self):
        self.drops_count = 0
        self.total_mass = 0.0
        self.is_dripping = False
        self.is_finished = False
        self.drop_radius = 0
        self.drop_y = 50
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx = w // 2

        # 1. Бюретка
        painter.setBrush(QColor(220, 220, 255))
        painter.setPen(Qt.black)
        painter.drawRect(cx - 10, 0, 20, 50)
        
        # 2. Тамчы
        if (self.is_dripping or self.drop_radius > 0) and not self.is_finished:
            painter.setBrush(QColor(100, 150, 255))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, self.drop_y), self.drop_radius, self.drop_radius * 1.2)

        # 3. Стакан
        beaker_y = 300
        beaker_w = 80
        beaker_h = 60
        painter.setBrush(QColor(240, 240, 255, 150))
        painter.setPen(Qt.black)
        painter.drawRect(cx - beaker_w//2, beaker_y, beaker_w, beaker_h)
        
        # Суунун деңгээли
        if self.drops_count > 0:
            level = min(beaker_h - 5, self.drops_count)
            painter.setBrush(QColor(100, 150, 255, 180))
            painter.setPen(Qt.NoPen)
            painter.drawRect(cx - beaker_w//2 + 2, beaker_y + beaker_h - level, beaker_w - 4, level)

        # 4. Тараза
        scale_y = beaker_y + beaker_h
        painter.setBrush(QColor(50, 50, 50))
        painter.drawRect(cx - 60, scale_y, 120, 40)
        painter.setBrush(QColor(200, 255, 200))
        painter.drawRect(cx - 40, scale_y + 10, 80, 20)
        
        # Масса
        mass_g = self.total_mass * 1000
        painter.setPen(Qt.black)
        painter.setFont(QFont("Courier", 12, QFont.Bold))
        painter.drawText(cx - 35, scale_y + 25, f"{mass_g:.3f} g")
        
        # Тамчылардын саны
        painter.setFont(QFont("Arial", 10))
        painter.drawText(cx + 70, beaker_y + 30, f"n = {self.drops_count}")

# ==========================================
# НЕГИЗГИ ТЕРЕЗЕ
# ==========================================
class LabSurfaceTensionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш №18: Беттик тартылуу")
        self.resize(1000, 600)
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СОЛ ЖАК ---
        left_group = QGroupBox("Тажрыйба стенди")
        left_layout = QVBoxLayout()
        self.stand = SurfaceTensionWidget(self) 
        left_layout.addWidget(self.stand)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- ОҢ ЖАК ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Тапшырма
        task_g = QGroupBox("Тапшырма")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. 'Баштоо' баскычын басып, 50 тамчы топтоңуз."))
        task_l.addWidget(QLabel("2. Жалпы массаны (M) жана тамчылардын санын (n) жазыңыз."))
        task_l.addWidget(QLabel("3. Бир тамчынын массасын (m = M/n) эсептеңиз."))
        task_l.addWidget(QLabel("4. Формула: σ = (m * g) / (π * d)"))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Параметрлер
        param_g = QGroupBox("Берилген маанилер")
        param_l = QVBoxLayout()
        self.lbl_d = QLabel("Түтүктүн диаметри: d = 2 мм (0.002 м)")
        self.lbl_g = QLabel("Эркин түшүү ылдамдануусу: g = 9.81 м/с²")
        param_l.addWidget(self.lbl_d)
        param_l.addWidget(self.lbl_g)
        param_g.setLayout(param_l)
        right_panel.addWidget(param_g)

        # 3. Башкаруу
        ctrl_g = QGroupBox("Башкаруу")
        ctrl_l = QVBoxLayout()
        
        self.btn_start = QPushButton("Баштоо (Тамчылатуу)")
        self.btn_start.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.btn_start.clicked.connect(self.toggle_drops)
        
        ctrl_l.addWidget(self.btn_start)
        ctrl_g.setLayout(ctrl_l)
        right_panel.addWidget(ctrl_g)

        # 4. Эсептөө
        calc_g = QGroupBox("Эсептөө")
        calc_l = QVBoxLayout()
        
        self.in_M = QLineEdit(); self.in_M.setPlaceholderText("Жалпы масса M (г)")
        self.in_n = QLineEdit(); self.in_n.setPlaceholderText("Тамчы саны n")
        self.in_sigma = QLineEdit(); self.in_sigma.setPlaceholderText("Коэффициент σ (Н/м)")
        
        btn_check = QPushButton("Текшерүү")
        btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_check.clicked.connect(self.check_answer)
        
        btn_new = QPushButton("Жаңы суюктук")
        btn_new.clicked.connect(self.new_experiment)
        
        calc_l.addWidget(QLabel("Өлчөнгөн маанилер:"))
        calc_l.addWidget(self.in_M)
        calc_l.addWidget(self.in_n)
        calc_l.addWidget(QLabel("Жооп:"))
        calc_l.addWidget(self.in_sigma)
        calc_l.addWidget(btn_check)
        calc_l.addWidget(btn_new)
        
        calc_g.setLayout(calc_l)
        right_panel.addWidget(calc_g)
        right_panel.addStretch(1)

    def new_experiment(self):
        liquids = [("Суу", 0.073), ("Спирт", 0.022), ("Глицерин", 0.063), ("Ацетон", 0.024)]
        name, sigma = random.choice(liquids)
        self.true_sigma = sigma
        self.stand.sigma = sigma
        self.stand.reset()
        
        self.in_M.clear(); self.in_n.clear(); self.in_sigma.clear()
        self.btn_start.setEnabled(True)
        self.btn_start.setText("Баштоо (Тамчылатуу)")
        self.btn_start.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        
        QMessageBox.information(self, "Жаңы", "Жаңы суюктук куюлду. Ишти баштаңыз.")

    def toggle_drops(self):
        self.stand.toggle_dripping()
        if self.stand.is_dripping:
            self.btn_start.setText("Токтотуу (Пауза)")
            self.btn_start.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        else:
            self.btn_start.setText("Улантуу (Тамчылатуу)")
            self.btn_start.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")

    def experiment_finished(self):
        self.btn_start.setText("Бүттү (50 тамчы)")
        self.btn_start.setEnabled(False)
        self.btn_start.setStyleSheet("background-color: #9E9E9E; color: white; font-weight: bold;")
        QMessageBox.information(self, "Бүттү", "50 тамчы топтолду! Таразадагы массаны жазып алыңыз.")

    def check_answer(self):
        try:
            val = float(self.in_sigma.text())
        except:
            QMessageBox.warning(self, "Ката", "Сан жазыңыз!")
            return
            
        if abs(val - self.true_sigma) < 0.005:
            QMessageBox.information(self, "Туура", f"✅ Азаматсыз! σ = {self.true_sigma} Н/м")
        else:
            QMessageBox.warning(self, "Ката", f"❌ Туура эмес. σ = {self.true_sigma} Н/м")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabSurfaceTensionApp()
    win.show()
    sys.exit(app.exec())