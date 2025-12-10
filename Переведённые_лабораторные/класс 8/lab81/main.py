# lab_mix_water.py
# Требуется: pip install PySide6
import sys, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer

class CalorimeterWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.hot_volume = 0
        self.cold_volume = 0
        self.hot_temp = 0
        self.cold_temp = 0
        self.final_temp = None
        self.mixed = False

    def set_params(self, m1,t1,m2,t2):
        self.hot_volume = m1
        self.hot_temp = t1
        self.cold_volume = m2
        self.cold_temp = t2
        self.final_temp = None
        self.mixed = False
        self.update()

    def mix(self):
        if self.hot_volume+self.cold_volume==0:
            self.final_temp = None
        else:
            self.final_temp = (self.hot_volume*self.hot_temp + self.cold_volume*self.cold_temp)/(self.hot_volume+self.cold_volume)
        self.mixed = True
        self.update()

    def paintEvent(self,event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w,h = self.width(), self.height()
        # сосуд
        p.setPen(QPen(Qt.black,2))
        p.setBrush(QColor(220,220,220))
        p.drawRect(w//4,h//4,w//2,h//2)
        # вода
        if self.mixed and self.final_temp is not None:
            color = QColor(100+int(self.final_temp*2),150,255-int(self.final_temp))
            p.setBrush(color)
            p.drawRect(w//4,h//2,w//2,h//4)
            # термометр
            p.setPen(QPen(Qt.black,1))
            p.setFont(QFont("Sans",14))
            p.drawText(w//2-40,h//2-60,f"T = {self.final_temp:.1f} °C")
        else:
            p.setFont(QFont("Sans",12))
            p.drawText(w//2-60,h//2-20,"Суу аралашпайт")

class LabMixApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык — Ыстуу жана салкын суунун аралашуусу")
        self.setMinimumSize(900,600)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left,2); main.addLayout(right,1)

        self.calorimeter = CalorimeterWidget()
        left.addWidget(self.calorimeter)

        right.addWidget(QLabel("<b>Ыстуу жана салкын суунун аралашуусу</b>"))
        info = QLabel("Ыстуу жана салкын суунун массаларын жана температураларын киргизиңиз.\n"
                      "Аралашуудан кийин термометр акыркы температураны көрсөтөт.")
        info.setWordWrap(True)
        right.addWidget(info)

        self.input_m1 = QLineEdit(); self.input_m1.setPlaceholderText("m1 (г)")
        self.input_t1 = QLineEdit(); self.input_t1.setPlaceholderText("t1 (°C)")
        self.input_m2 = QLineEdit(); self.input_m2.setPlaceholderText("m2 (г)")
        self.input_t2 = QLineEdit(); self.input_t2.setPlaceholderText("t2 (°C)")
        self.input_t = QLineEdit(); self.input_t.setPlaceholderText("t (°C) — сиздин жоопуңуз")
        right.addWidget(self.input_m1)
        right.addWidget(self.input_t1)
        right.addWidget(self.input_m2)
        right.addWidget(self.input_t2)
        right.addWidget(self.input_t)

        btn_mix = QPushButton("Аралаштыруу")
        btn_mix.clicked.connect(self.mix)
        btn_check = QPushButton("Текшерүү")
        btn_check.clicked.connect(self.check)
        btn_show = QPushButton("Жоопту көрсөтүү")
        btn_show.clicked.connect(self.show_answer)
        btn_random = QPushButton("Кездейсоқ таажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        btn_reset = QPushButton("Сброс")
        btn_reset.clicked.connect(self.reset)

        right.addWidget(btn_mix)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        self.lbl_result = QLabel("")
        right.addWidget(self.lbl_result)
        right.addStretch(1)

        self.random_experiment()

    def mix(self):
        try:
            m1 = float(self.input_m1.text())
            t1 = float(self.input_t1.text())
            m2 = float(self.input_m2.text())
            t2 = float(self.input_t2.text())
        except:
            QMessageBox.warning(self,"Ката","m1, t1, m2, t2 үчүн сандык маанилерди киргизиңиз.")
            return
        self.calorimeter.set_params(m1,t1,m2,t2)
        self.calorimeter.mix()

    def check(self):
        if self.calorimeter.final_temp is None:
            QMessageBox.information(self,"Инфо","Адегечү сууну аралаштырыңыз.")
            return
        try:
            t_user = float(self.input_t.text())
        except:
            QMessageBox.warning(self,"Ката","Сиздин жоопуңузду киргизиңиз t.")
            return
        t_true = self.calorimeter.final_temp
        tol = 0.5
        if abs(t_user-t_true)<=tol:
            self.lbl_result.setText("✅ Жооп туура.")
        else:
            self.lbl_result.setText(f"❌ Туура эмес. Туура t = {t_true:.1f} °C")

    def show_answer(self):
        if self.calorimeter.final_temp is None:
            QMessageBox.information(self,"Инфо","Адегечү сууну аралаштырыңыз.")
            return
        self.input_t.setText(f"{self.calorimeter.final_temp:.1f}")
        self.lbl_result.setText("Туура жооп көрсөтүлдү.")

    def random_experiment(self):
        m1 = random.randint(50,200)
        t1 = random.randint(40,90)
        m2 = random.randint(50,200)
        t2 = random.randint(5,30)
        self.input_m1.setText(str(m1))
        self.input_t1.setText(str(t1))
        self.input_m2.setText(str(m2))
        self.input_t2.setText(str(t2))
        self.calorimeter.set_params(m1,t1,m2,t2)

    def reset(self):
        self.input_m1.clear(); self.input_t1.clear()
        self.input_m2.clear(); self.input_t2.clear()
        self.input_t.clear()
        self.calorimeter.set_params(0,0,0,0)
        self.lbl_result.setText("")

if __name__=="__main__":
    app = QApplication(sys.argv)
    win = LabMixApp()
    win.show()
    sys.exit(app.exec())
