# lab09_lever.py
# Требуется: pip install PySide6
import sys
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygon
from PySide6.QtCore import Qt, QTimer, QPointF, QPoint

G = 9.81  # м/с^2

class Weight:
    def __init__(self, mass, pos_index):
        """
        pos_index: целое число от -5 до 5 (позиция на рычаге).
        mass: масса в граммах.
        """
        self.mass = mass
        self.pos_index = pos_index
        self.r = 14 + int(mass / 50)  # радиус зависит от массы
        self.color = QColor(100, 100, 200) if mass < 100 else QColor(200, 100, 100)

class LeverWidget(QFrame):
    """
    Виджет рычага.
    Рычаг имеет деления (плечи) от -5 до +5.
    Грузы можно вешать на конкретные деления.
    Рычаг наклоняется, если моменты сил не равны.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Состояние рычага
        self.angle = 0.0        # текущий угол (радианы)
        self.target_angle = 0.0 # целевой угол
        self.velocity = 0.0
        
        # Грузы на рычаге
        self.weights = []
        
        # Анимация
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def add_weight(self, mass, position):
        """Добавить груз заданной массы на позицию (-5..5)"""
        if -5 <= position <= 5 and position != 0:
            self.weights.append(Weight(mass, position))
            self._update_balance()
            self.update()

    def clear_weights(self):
        self.weights = []
        self._update_balance()
        self.update()

    def _update_balance(self):
        # Расчет моментов сил
        # M = m * g * L
        moment_sum = 0
        for w in self.weights:
            # L - это w.pos_index. Слева (-), справа (+).
            # Чтобы момент слева был против часовой (положительный в физике часто, но здесь зависит от оси),
            # а справа по часовой.
            # Пусть момент = m * pos.
            # Если сумма 0 -> равновесие.
            # Если сумма > 0 -> перевес вправо (угол положительный).
            # Если сумма < 0 -> перевес влево (угол отрицательный).
            moment_sum += w.mass * w.pos_index

        if moment_sum == 0:
            self.target_angle = 0.0
        elif moment_sum > 0:
            self.target_angle = math.radians(20) # наклон вправо
        else:
            self.target_angle = math.radians(-20) # наклон влево

    def animate(self):
        # Простая анимация поворота
        diff = self.target_angle - self.angle
        if abs(diff) > 0.001:
            self.angle += diff * 0.1
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        
        cx = w // 2
        cy = h // 2 + 50
        
        # 1. Опора (Треугольник)
        painter.setBrush(QColor(80, 80, 80))
        painter.setPen(QPen(Qt.black, 2))
        triangle = QPolygon([
            QPoint(cx, cy),
            QPoint(cx - 20, cy + 40),
            QPoint(cx + 20, cy + 40)
        ])
        painter.drawPolygon(triangle)
        
        # --- Трансформация для рычага ---
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(math.degrees(self.angle))
        
        # 2. Балка рычага
        beam_len = 500
        beam_h = 14
        step = beam_len // 12 # шаг делений (5 слева, 5 справа + запасы)
        
        painter.setBrush(QColor(220, 180, 120)) # Дерево
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(-beam_len//2, -beam_h//2, beam_len, beam_h)
        
        # 3. Деления и крючки
        painter.setPen(QPen(Qt.black, 2))
        font = QFont("Sans", 10, QFont.Bold)
        painter.setFont(font)
        
        for i in range(-5, 6):
            if i == 0: continue
            x = i * 40 # шаг 40 пикселей
            
            # Риска
            painter.drawLine(x, -beam_h//2, x, beam_h//2)
            
            # Крючок снизу
            painter.drawLine(x, beam_h//2, x, beam_h//2 + 5)
            painter.drawArc(x - 3, beam_h//2 + 5, 6, 6, 0, -180 * 16)
            
            # Цифра (номер плеча)
            painter.drawText(x - 5, -beam_h//2 - 5, str(abs(i)))

        # 4. Грузы
        for w in self.weights:
            x = w.pos_index * 40
            # Груз висит на нитке
            painter.setPen(QPen(Qt.black, 1))
            painter.drawLine(x, beam_h//2 + 8, x, beam_h//2 + 40)
            
            # Сам груз
            painter.setBrush(w.color)
            painter.drawRect(x - 12, beam_h//2 + 40, 24, 30)
            painter.setPen(Qt.white)
            painter.drawText(x - 10, beam_h//2 + 60, f"{w.mass}")

        painter.restore()
        
        # Текст состояния
        painter.setPen(Qt.black)
        painter.setFont(QFont("Sans", 14))
        state_text = "Тең салмактуулук" if abs(self.angle) < 0.01 else "Тең салмактуулук жок"
        painter.drawText(20, 40, f"Абалы: {state_text}")


class LabLeverApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш №9: Рычагтын тең салмактуу абалда болуу шартын айкындоо")
        self.setMinimumSize(1000, 600)

        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

        # Визуализация
        self.lever = LeverWidget()
        left_layout.addWidget(self.lever)

        # Панель управления
        lbl_title = QLabel("<b>Рычагтын тең салмактуу абалда болуу шартын айкындоо</b>")
        lbl_title.setFont(QFont("Sans", 14))
        right_layout.addWidget(lbl_title)

        lbl_desc = QLabel(
            "Рычаг тең салмактуулукта болушу үчүн моменттердин эрежесин аткаруу керек:\n"
            "M1 = M2  =>  F1 · L1 = F2 · L2\n"
            "Жүктөрдү илип, рычагды тең салмакка келтириңиз."
        )
        lbl_desc.setWordWrap(True)
        right_layout.addWidget(lbl_desc)

        # Группы добавления грузов
        # Левая часть
        group_left = QFrame()
        group_left.setFrameShape(QFrame.StyledPanel)
        lay_left = QVBoxLayout(group_left)
        lay_left.addWidget(QLabel("<b>Сол ийин (L1)</b>"))
        
        self.input_m1 = QLineEdit()
        self.input_m1.setPlaceholderText("Масса m1 (г)")
        lay_left.addWidget(self.input_m1)
        
        self.input_l1 = QLineEdit()
        self.input_l1.setPlaceholderText("Ийин L1 (1-5)")
        lay_left.addWidget(self.input_l1)
        
        btn_add_left = QPushButton("Сол жакка кошуу")
        btn_add_left.clicked.connect(self.add_left)
        lay_left.addWidget(btn_add_left)
        right_layout.addWidget(group_left)

        # Правая часть
        group_right = QFrame()
        group_right.setFrameShape(QFrame.StyledPanel)
        lay_right = QVBoxLayout(group_right)
        lay_right.addWidget(QLabel("<b>Оң ийин (L2)</b>"))
        
        self.input_m2 = QLineEdit()
        self.input_m2.setPlaceholderText("Масса m2 (г)")
        lay_right.addWidget(self.input_m2)
        
        self.input_l2 = QLineEdit()
        self.input_l2.setPlaceholderText("Ийин L2 (1-5)")
        lay_right.addWidget(self.input_l2)
        
        btn_add_right = QPushButton("Оң жакка кошуу")
        btn_add_right.clicked.connect(self.add_right)
        lay_right.addWidget(btn_add_right)
        right_layout.addWidget(group_right)

        # Управление
        btn_clear = QPushButton("Тазалоо (Бардыгын алуу)")
        btn_clear.setStyleSheet("background-color: #ffcccc;")
        btn_clear.clicked.connect(self.lever.clear_weights)
        right_layout.addWidget(btn_clear)

        right_layout.addSpacing(20)
        right_layout.addWidget(QLabel("<b>Эсептөө жана Текшерүү</b>"))
        
        self.input_answer = QLineEdit()
        self.input_answer.setPlaceholderText("Моментти киргизиңиз (г·см)")
        right_layout.addWidget(self.input_answer)
        
        btn_check = QPushButton("Текшерүү")
        btn_check.clicked.connect(self.check_answer)
        right_layout.addWidget(btn_check)

        right_layout.addStretch()

    def add_left(self):
        self._add_weight(self.input_m1, self.input_l1, is_left=True)

    def add_right(self):
        self._add_weight(self.input_m2, self.input_l2, is_left=False)

    def _add_weight(self, input_m, input_l, is_left):
        try:
            m = float(input_m.text())
            l = int(input_l.text())
        except ValueError:
            QMessageBox.warning(self, "Ката", "Масса жана ийин үчүн сан маанилерин киргизиңиз.")
            return
        
        if l < 1 or l > 5:
            QMessageBox.warning(self, "Ката", "Ийин 1ден 5ке чейин болушу керек.")
            return

        # Для левой стороны индекс отрицательный, для правой положительный
        pos_index = -l if is_left else l
        self.lever.add_weight(m, pos_index)

    def check_answer(self):
        # Проверка условия равновесия пользователем
        # Пусть пользователь введет момент одной из сил (например, M1 = m1*l1)
        # Это упрощенная проверка, так как грузов может быть много.
        # Лучше спросить: "Рычаг тең салмактуулуктабы?" (Да/Нет)
        # Но для разнообразия оставим поле ввода.
        
        # Рассчитаем реальный баланс
        moment_sum = 0
        for w in self.lever.weights:
            moment_sum += w.mass * w.pos_index
            
        is_balanced = (moment_sum == 0)
        
        if is_balanced:
            QMessageBox.information(self, "Жыйынтык", "✅ Рычаг тең салмактуулукта!\nСиз туура кылдыңыз.")
        else:
            if moment_sum > 0:
                side = "Оң жагы"
            else:
                side = "Сол жагы"
            QMessageBox.warning(self, "Жыйынтык", f"❌ Тең салмактуулук жок.\n{side} оор тартып жатат.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabLeverApp()
    win.show()
    sys.exit(app.exec())