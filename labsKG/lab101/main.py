import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSlider, QSpinBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Катушка + Магнит
# ==========================================
class InductionWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 350)
        self.setStyleSheet("background-color: #f8f9fa; border: 1px solid #ccc; border-radius: 8px;")
        
        self.N = 100          
        self.speed = 0        
        self.magnet_x = 50    
        self.is_running = False
        
        self.current_voltage = 0.0
        self.max_voltage_measured = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16) 

    def start_experiment(self, n_turns, speed_val):
        self.N = n_turns
        self.speed = speed_val
        self.magnet_x = 50
        self.is_running = True
        self.max_voltage_measured = 0.0
        self.update()

    def pause_experiment(self):
        # Анимацияны токтотуу же улантуу
        self.is_running = not self.is_running
        self.update()

    def animate(self):
        if not self.is_running:
            # Эгер токтоп турса, эч нерсе кылбайт (токту өчүрбөйбүз, токтогон жерде турат)
            return

        self.magnet_x += self.speed * 0.5
        
        coil_center = self.width() / 2
        dist = (self.magnet_x - coil_center) / 100.0 
        
        field_change = -2 * dist * math.exp(-(dist**2))
        raw_emf = -self.N * (self.speed / 10.0) * field_change
        
        self.current_voltage = raw_emf
        
        if abs(self.current_voltage) > self.max_voltage_measured:
            self.max_voltage_measured = abs(self.current_voltage)

        if self.magnet_x > self.width() + 100:
            self.is_running = False
            self.magnet_x = self.width() + 100
            self.current_voltage = 0 # Чыгып кеткенде 0 болот
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cy = h // 2
        cx = w // 2

        # 1. Катушка
        coil_w = 120
        coil_h = 140
        painter.setBrush(QColor(220, 200, 180))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(cx - coil_w//2, cy - coil_h//2, coil_w, coil_h)
        
        painter.setPen(QPen(QColor(184, 115, 51), 2))
        lines = min(20, self.N // 10)
        step = coil_w / lines
        for i in range(lines):
            x = cx - coil_w//2 + i * step
            painter.drawEllipse(int(x), int(cy - coil_h//2), int(step), int(coil_h))

        # 2. Магнит
        mag_w = 80
        mag_h = 40
        mag_y = cy - mag_h // 2
        
        painter.setBrush(QColor(220, 50, 50))
        painter.setPen(Qt.black)
        painter.drawRect(int(self.magnet_x), int(mag_y), mag_w//2, mag_h)
        painter.setPen(Qt.white)
        painter.drawText(int(self.magnet_x + 5), int(mag_y + 25), "N")
        
        painter.setBrush(QColor(50, 50, 220))
        painter.setPen(Qt.black)
        painter.drawRect(int(self.magnet_x - mag_w//2), int(mag_y), mag_w//2, mag_h)
        painter.setPen(Qt.white)
        painter.drawText(int(self.magnet_x - 30), int(mag_y + 25), "S")

        # 3. Гальванометр
        g_r = 60
        g_x = w - 80
        g_y = 80
        
        painter.setBrush(QColor(240, 240, 240))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawEllipse(QPointF(g_x, g_y), g_r, g_r)
        
        painter.drawText(g_x - 10, g_y + 30, "mV")
        
        angle = (self.current_voltage / 500.0) * 90 
        if angle > 90: angle = 90
        if angle < -90: angle = -90
        
        painter.save()
        painter.translate(g_x, g_y)
        painter.rotate(angle)
        painter.setPen(QPen(Qt.red, 3))
        painter.drawLine(0, 0, 0, -50)
        painter.restore()
        
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(g_x - 20, g_y + 80, f"{self.current_voltage:.1f}")

# ==========================================
# НЕГИЗГИ ТЕРЕЗЕ
# ==========================================
class LabInductionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш №16: Электромагниттик индукция")
        self.resize(1100, 650)
        self.setup_ui()

    def setup_ui(self):
        main = QHBoxLayout(self)

        # --- СОЛ ЖАК: Стенд ---
        left_group = QGroupBox("Тажрыйба стенди")
        left_layout = QVBoxLayout()
        self.ind_widget = InductionWidget()
        left_layout.addWidget(self.ind_widget)
        left_group.setLayout(left_layout)
        main.addWidget(left_group, 2)

        # --- ОҢ ЖАК: Башкаруу ---
        right_panel = QVBoxLayout()
        main.addLayout(right_panel, 1)

        # 1. Тапшырма
        task_g = QGroupBox("Тапшырма")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. 'Баштоо' баскычын басыңыз."))
        task_l.addWidget(QLabel("2. Стрелка эң көп кыйшайган учурда 'Пауза' басыңыз."))
        task_l.addWidget(QLabel("3. Маанини жазып алып, 'Улантуу' менен экспериментти бүтүрүңүз."))
        task_g.setLayout(task_l)
        right_panel.addWidget(task_g)

        # 2. Параметрлер
        ctrl_g = QGroupBox("Параметрлер")
        ctrl_l = QVBoxLayout()
        
        self.spin_n = QSpinBox()
        self.spin_n.setRange(50, 500)
        self.spin_n.setValue(100)
        self.spin_n.setSingleStep(50)
        
        self.slider_v = QSlider(Qt.Horizontal)
        self.slider_v.setRange(10, 50)
        self.slider_v.setValue(20)
        self.lbl_v = QLabel("Ылдамдык: 20 м/с")
        self.slider_v.valueChanged.connect(lambda v: self.lbl_v.setText(f"Ылдамдык: {v} м/с"))
        
        # Баштоо жана Пауза баскычтары
        h_btns = QHBoxLayout()
        btn_start = QPushButton("Баштоо")
        btn_start.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_start.clicked.connect(self.run_experiment)
        
        btn_pause = QPushButton("Пауза / Улантуу")
        btn_pause.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        btn_pause.clicked.connect(self.pause_experiment)
        
        h_btns.addWidget(btn_start)
        h_btns.addWidget(btn_pause)
        
        ctrl_l.addWidget(QLabel("Ороолордун саны (N):"))
        ctrl_l.addWidget(self.spin_n)
        ctrl_l.addWidget(self.lbl_v)
        ctrl_l.addWidget(self.slider_v)
        ctrl_l.addLayout(h_btns)
        ctrl_g.setLayout(ctrl_l)
        right_panel.addWidget(ctrl_g)

        # 3. Жыйынтыктарды жазуу
        res_g = QGroupBox("Жыйынтыктарды талдоо")
        res_l = QVBoxLayout()
        
        self.in_umax = QLineEdit()
        self.in_umax.setPlaceholderText("U_max (Паузада окулган маани)")
        
        btn_add = QPushButton("Текшерүү жана кошуу")
        btn_add.clicked.connect(self.check_and_add)
        
        res_l.addWidget(QLabel("Байкалган максималдуу чыңалуу:"))
        res_l.addWidget(self.in_umax)
        res_l.addWidget(btn_add)
        res_g.setLayout(res_l)
        right_panel.addWidget(res_g)

        # 4. Таблица
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["N (ороо)", "v (ылдамдык)", "U_max (мВ)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_panel.addWidget(self.table)

    def run_experiment(self):
        n = self.spin_n.value()
        v = self.slider_v.value()
        self.ind_widget.start_experiment(n, v)

    def pause_experiment(self):
        self.ind_widget.pause_experiment()

    def check_and_add(self):
        try:
            u_user = float(self.in_umax.text())
        except:
            QMessageBox.warning(self, "Ката", "Сан жазыңыз!")
            return
            
        real_u = self.ind_widget.max_voltage_measured
        
        if real_u == 0:
            QMessageBox.warning(self, "Ката", "Адегенде экспериментти баштаңыз!")
            return

        if abs(u_user - real_u) <= real_u * 0.15:
            QMessageBox.information(self, "Туура", "✅ Маани туура окулду! Таблицага кошулду.")
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(self.spin_n.value())))
            self.table.setItem(row, 1, QTableWidgetItem(str(self.slider_v.value())))
            self.table.setItem(row, 2, QTableWidgetItem(f"{real_u:.1f}"))
            self.in_umax.clear()
        else:
            QMessageBox.warning(self, "Ката", f"❌ Туура эмес. Гальванометр {real_u:.1f} деп көрсөттү.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabInductionApp()
    win.show()
    sys.exit(app.exec())