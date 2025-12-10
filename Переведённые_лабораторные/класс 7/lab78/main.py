# lab_lever.py
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer, QPointF

class LeverWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 300)
        self.beam_length = 400
        self.center = QPointF(self.width()/2, 150)
        self.angle = 0.0
        self.target_angle = 0.0
        self.weights_left = []
        self.weights_right = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def add_weight(self, side, mass, distance):
        if side == 'left':
            self.weights_left.append((mass, distance))
        else:
            self.weights_right.append((mass, distance))
        self._recompute_angle()

    def clear_weights(self):
        self.weights_left.clear()
        self.weights_right.clear()
        self._recompute_angle()

    def _recompute_angle(self):
        M_left = sum(m*d for m,d in self.weights_left)
        M_right = sum(m*d for m,d in self.weights_right)
        diff = M_right - M_left
        max_angle = math.radians(15)
        self.target_angle = max(-max_angle, min(max_angle, diff/200.0))

    def animate(self):
        da = self.target_angle - self.angle
        if abs(da) > 0.0005:
            self.angle += da * 0.1
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w,h = self.width(), self.height()
        self.center = QPointF(w/2, h/2)
        # опора
        painter.setPen(QPen(Qt.black,2))
        painter.setBrush(QColor(160,160,160))
        painter.drawPolygon([
            QPointF(self.center.x()-20,self.center.y()+60),
            QPointF(self.center.x()+20,self.center.y()+60),
            QPointF(self.center.x(),self.center.y())
        ])
        # балка
        painter.save()
        painter.translate(self.center)
        painter.rotate(math.degrees(self.angle))
        painter.setPen(QPen(Qt.black,3))
        painter.setBrush(QColor(220,220,240))
        painter.drawRect(-self.beam_length/2,-8,self.beam_length,16)
        # точки подвеса
        for m,d in self.weights_left:
            x = -d
            painter.setBrush(QColor(180,80,80))
            painter.drawEllipse(QPointF(x,20),10,10)
            painter.drawText(x-10,40,f"{m}N")
        for m,d in self.weights_right:
            x = d
            painter.setBrush(QColor(80,180,80))
            painter.drawEllipse(QPointF(x,20),10,10)
            painter.drawText(x-10,40,f"{m}N")
        painter.restore()

class LabLeverApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык — Рычаг жана теңдөө шарты")
        self.setMinimumSize(1000,600)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left,2); main.addLayout(right,1)

        self.lever = LeverWidget()
        left.addWidget(self.lever)

        right.addWidget(QLabel("<b>Рычаг жана теңдөө шарты</b>"))
        info = QLabel("Сол жана оң жакка күчтөрдү кошуңуз.\n"
                      "Шартты текшериңиз: F1·L1 = F2·L2.")
        info.setWordWrap(True)
        right.addWidget(info)

        self.input_F1 = QLineEdit(); self.input_F1.setPlaceholderText("Күч F1, Н")
        self.input_L1 = QLineEdit(); self.input_L1.setPlaceholderText("Рычаг L1, см")
        self.input_F2 = QLineEdit(); self.input_F2.setPlaceholderText("Күч F2, Н")
        self.input_L2 = QLineEdit(); self.input_L2.setPlaceholderText("Рычаг L2, см")
        right.addWidget(self.input_F1)
        right.addWidget(self.input_L1)
        right.addWidget(self.input_F2)
        right.addWidget(self.input_L2)

        btn_add_left = QPushButton("Сол жакка жүк кошуу")
        btn_add_left.clicked.connect(self.add_left)
        btn_add_right = QPushButton("Оң жакка жүк кошуу")
        btn_add_right.clicked.connect(self.add_right)
        btn_clear = QPushButton("Тазалоо")
        btn_clear.clicked.connect(self.clear)
        btn_check = QPushButton("Шартты текшерүү")
        btn_check.clicked.connect(self.check)
        btn_random = QPushButton("Кездейсоқ таажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        btn_show = QPushButton("Жоопту көрсөтүү")
        btn_show.clicked.connect(self.show_answer)

        right.addWidget(btn_add_left)
        right.addWidget(btn_add_right)
        right.addWidget(btn_clear)
        right.addWidget(btn_check)
        right.addWidget(btn_random)
        right.addWidget(btn_show)

        self.lbl_result = QLabel("")
        right.addWidget(self.lbl_result)
        right.addStretch(1)

        self._generate_experiment()

    def _generate_experiment(self):
        self.F1_true = random.randint(1,20)
        self.L1_true = random.randint(10,50)
        self.F2_true = random.randint(1,20)
        self.L2_true = int((self.F1_true*self.L1_true)/self.F2_true)
        self.lever.clear_weights()
        self.lever.add_weight('left',self.F1_true,self.L1_true)
        self.lever.add_weight('right',self.F2_true,self.L2_true)

    def add_left(self):
        try:
            F = float(self.input_F1.text())
            L = float(self.input_L1.text())
        except:
            QMessageBox.warning(self,"Ката","F1 жана L1 киргизиңиз.")
            return
        self.lever.add_weight('left',F,L)

    def add_right(self):
        try:
            F = float(self.input_F2.text())
            L = float(self.input_L2.text())
        except:
            QMessageBox.warning(self,"Ката","F2 жана L2 киргизиңиз.")
            return
        self.lever.add_weight('right',F,L)

    def clear(self):
        self.lever.clear_weights()
        self.lbl_result.setText("")

    def check(self):
        try:
            F1 = float(self.input_F1.text())
            L1 = float(self.input_L1.text())
            F2 = float(self.input_F2.text())
            L2 = float(self.input_L2.text())
        except:
            QMessageBox.warning(self,"Ката","Бардык маанилерди киргизиңиз.")
            return
        left_moment = F1*L1
        right_moment = F2*L2
        if abs(left_moment-right_moment) < 0.5:
            self.lbl_result.setText("✅ Теңдөө шарты аткарылды.")
        else:
            self.lbl_result.setText(f"❌ Теңдөө жок. F1·L1={left_moment:.1f}, F2·L2={right_moment:.1f}")

    def random_experiment(self):
        self._generate_experiment()
        self.lbl_result.setText("Кездейсоқ таажрыйба түзүлдү.")

    def show_answer(self):
        self.input_F1.setText(str(self.F1_true))
        self.input_L1.setText(str(self.L1_true))
        self.input_F2.setText(str(self.F2_true))
        self.input_L2.setText(str(self.L2_true))
        self.lbl_result.setText("Туура маанилер көрсөтүлдү.")

if __name__=="__main__":
    app = QApplication(sys.argv)
    win = LabLeverApp()
    win.show()
    sys.exit(app.exec())
