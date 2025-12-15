# lab_friction.py
# Требуется: pip install PySide6
import sys, math, random, time
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QSpinBox,
    QTableWidget, QTableWidgetItem, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer

g = 9.81

# --- Виджет: тело на поверхности ---
class BodyWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 300)
        self.mass = 10
        self.mu = 0.3
        self.x = 20
        self.speed = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(40)

    def set_params(self, m=None, mu=None):
        if m is not None: self.mass = m
        if mu is not None: self.mu = mu
        self.x = 20
        self.speed = 20.0
        self.update()

    def _tick(self):
        # сила трения
        Ftr = self.mu * self.mass * g
        # простая модель: скорость уменьшается от трения
        self.speed -= Ftr/500.0
        if self.speed < 0: self.speed = 0
        self.x += self.speed*0.5
        if self.x > self.width()-100: self.x = self.width()-100
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(240,240,240))
        ground_y = self.height()-50
        p.fillRect(0, ground_y, self.width(), 10, QColor(120,120,120))
        # тело
        w,h = 80,50
        p.setBrush(QColor(100,150,200))
        p.drawRect(int(self.x), ground_y-h, w,h)
        p.setFont(QFont("Sans",9))
        p.drawText(int(self.x), ground_y-h-5, f"m={self.mass} кг, μ={self.mu}")

# --- Главное приложение ---
class LabFrictionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа — Сила трения (7 класс)")
        self.setMinimumSize(1000, 600)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left,2); main.addLayout(right,1)

        # Виджет анимации
        self.body = BodyWidget()
        left.addWidget(self.body)

        # Правая панель: параметры
        right.addWidget(QLabel("<b>Параметры эксперимента</b>"))
        right.addWidget(QLabel("Масса тела (кг)"))
        self.slider_m = QSlider(Qt.Horizontal); self.slider_m.setRange(1,50); self.slider_m.setValue(10)
        self.slider_m.valueChanged.connect(self.on_mass_change)
        right.addWidget(self.slider_m)
        self.lbl_m = QLabel("m = 10 кг"); right.addWidget(self.lbl_m)

        right.addWidget(QLabel("Коэффициент трения μ"))
        self.spin_mu = QSpinBox(); self.spin_mu.setRange(1,100); self.spin_mu.setValue(30)
        right.addWidget(self.spin_mu)

        # Поля ученика
        right.addSpacing(6)
        right.addWidget(QLabel("<b>Поля ученика (введите расчёты)</b>"))
        self.input_Ftr = QLineEdit(); self.input_Ftr.setPlaceholderText("Fтр (Н) — ваш расчёт")
        self.input_P = QLineEdit(); self.input_P.setPlaceholderText("P (Па) — ваш расчёт")
        right.addWidget(self.input_Ftr); right.addWidget(self.input_P)

        # Кнопки
        btn_apply = QPushButton("Применить параметры"); btn_apply.clicked.connect(self.apply_params)
        btn_random = QPushButton("Случайный эксперимент"); btn_random.clicked.connect(self.random_experiment)
        btn_check = QPushButton("Проверить ответы"); btn_check.clicked.connect(self.check)
        btn_show = QPushButton("Показать ответ"); btn_show.clicked.connect(self.show_answer)
        btn_reset = QPushButton("Сброс"); btn_reset.clicked.connect(self.reset_all)
        right.addWidget(btn_apply); right.addWidget(btn_random)
        right.addWidget(btn_check); right.addWidget(btn_show); right.addWidget(btn_reset)

        # Таблица результатов
        self.table = QTableWidget(0,5)
        self.table.setHorizontalHeaderLabels(["m (кг)","μ","Fтр (Н)","P (Па)","Результат"])
        right.addWidget(self.table)

        self.lbl_feedback = QLabel(""); self.lbl_feedback.setWordWrap(True)
        right.addWidget(self.lbl_feedback); right.addStretch(1)

        # старт
        self.random_experiment()

    def on_mass_change(self,val):
        self.lbl_m.setText(f"m = {val} кг")

    def apply_params(self):
        m = self.slider_m.value()
        mu = self.spin_mu.value()/100.0
        self.body.set_params(m=m, mu=mu)
        self.lbl_feedback.setText("Параметры применены.")

    def random_experiment(self):
        m = random.randint(5,30)
        mu = random.choice([0.1,0.2,0.3,0.4,0.5])
        self.slider_m.setValue(m)
        self.spin_mu.setValue(int(mu*100))
        self.body.set_params(m=m, mu=mu)
        self.input_Ftr.clear(); self.input_P.clear()
        self.lbl_feedback.setText(f"Случайный эксперимент: m={m} кг, μ={mu}. Рассчитайте Fтр и P.")

    def check(self):
        try:
            F_user = float(self.input_Ftr.text())
            P_user = float(self.input_P.text())
        except:
            QMessageBox.warning(self,"Ошибка","Введите числовые значения.")
            return
        m = self.slider_m.value()
        mu = self.spin_mu.value()/100.0
        F_true = mu * m * g
        P_true = (m*g)/0.01  # условная площадь 0.01 м²
        ok_F = abs(F_user - F_true) <= 0.05*F_true
        ok_P = abs(P_user - P_true) <= 0.05*P_true
        result = "✅ Всё верно" if ok_F and ok_P else f"❌ Ошибка (Fтр={F_true:.1f} Н, P={P_true:.1f} Па)"
        QMessageBox.information(self,"Результат",result)
        row = self.table.rowCount(); self.table.insertRow(row)
        self.table.setItem(row,0,QTableWidgetItem(str(m)))
        self.table.setItem(row,1,QTableWidgetItem(str(mu)))
        self.table.setItem(row,2,QTableWidgetItem(f"{F_true:.1f}"))
        self.table.setItem(row,3,QTableWidgetItem(f"{P_true:.1f}"))
        self.table.setItem(row,4,QTableWidgetItem(result))

    def show_answer(self):
        m = self.slider_m.value()
        mu = self.spin_mu.value()/100.0
        F_true = mu * m * g
        P_true = (m*g)/0.01
        self.input_Ftr.setText(f"{F_true:.1f}")
        self.input_P.setText(f"{P_true:.1f}")
        self.lbl_feedback.setText("Показаны правильные значения.")

    def reset_all(self):
        self.slider_m.setValue(10); self.spin_mu.setValue(30)
        self.body.set_params(m=10, mu=0.3)
        self.input_Ftr.clear(); self.input_P.clear()
        self.lbl_feedback.setText("Сброс выполнен.")

if __name__=="__main__":
    app = QApplication(sys.argv)
    win = LabFrictionApp()
    win.show()
    sys.exit(app.exec())
