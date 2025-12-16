import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox,
    QTextEdit, QSizePolicy, QScrollBar
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QAction
from PySide6.QtCore import Qt, QTimer, QPointF

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Линейка
# ==========================================
class RulerWidget(QFrame):
    def __init__(self, length_mm=200, px_per_mm=2.5, parent=None):
        super().__init__(parent)
        self.length_mm = length_mm
        self.px_per_mm = px_per_mm
        self.setMinimumWidth(int(self.length_mm * self.px_per_mm) + 60)
        self.setMinimumHeight(100)
        self.setStyleSheet("background-color: white; border-bottom: 1px solid #ccc;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        left = 20
        top = 20
        
        # Корпус линейки
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QColor(255, 235, 205)) # цвет дерева
        painter.drawRect(left, top, int(self.length_mm * self.px_per_mm), 40)
        
        # Деления и цифры
        painter.setPen(QPen(Qt.black, 1))
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        
        for mm in range(0, self.length_mm + 1):
            x = left + mm * self.px_per_mm
            if mm % 10 == 0:
                # Большое деление
                painter.drawLine(int(x), top + 40, int(x), top + 40 - 15)
                # Цифра
                text_rect = painter.fontMetrics().boundingRect(str(mm))
                painter.drawText(int(x - text_rect.width()/2), top + 15, f"{mm}")
            elif mm % 5 == 0:
                # Среднее деление
                painter.drawLine(int(x), top + 40, int(x), top + 40 - 10)
            else:
                # Малое деление
                painter.drawLine(int(x), top + 40, int(x), top + 40 - 5)

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Поле с шариками
# ==========================================
class BallsRowWidget(QFrame):
    def __init__(self, ruler_widget: RulerWidget, parent=None):
        super().__init__(parent)
        self.ruler = ruler_widget
        self.setMinimumSize(700, 200)
        self.setStyleSheet("background-color: #f0f8ff; border: 1px solid #ccc; border-top: none;")
        
        self.balls = []
        self.ball_radius = 12
        self.row_y = 100
        self.drag_index = None
        
        # Таймер анимации
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        
        self._create_random_row()

    def _create_random_row(self):
        n = random.randint(6, 15)
        left = 40
        # Не выходим за пределы линейки
        max_width = int(self.ruler.length_mm * self.ruler.px_per_mm)
        right = max(self.width() - 40, max_width)
        
        spacing = (right - left) / (n + 1)
        self.balls = []
        for i in range(n):
            x = left + (i + 1) * spacing + random.uniform(-10, 10)
            y = self.row_y + random.uniform(-10, 10)
            self.balls.append({'pos': QPointF(x, y), 'r': self.ball_radius, 'target_x': x})

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Центральная ось (пунктир)
        painter.setPen(QPen(Qt.gray, 1, Qt.DashLine))
        painter.drawLine(10, self.row_y, self.width() - 10, self.row_y)
        
        # Рисуем шарики
        for i, b in enumerate(self.balls):
            pos = b['pos']
            r = b['r']
            
            # Тень
            painter.setBrush(QColor(0, 0, 0, 30))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(pos.x()+2, pos.y()+2), r, r)
            
            # Шарик
            painter.setBrush(QColor(220, 60, 60)) # Красный
            painter.setPen(QPen(Qt.black, 1))
            painter.drawEllipse(pos, r, r)
            
            # Номер
            painter.setPen(QPen(Qt.white, 1))
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            text = str(i+1)
            rect = painter.fontMetrics().boundingRect(text)
            painter.drawText(pos.x() - rect.width()/2, pos.y() + rect.height()/3, text)

        # Рисуем размерную линию (L)
        if len(self.balls) >= 2:
            xs = sorted([b['pos'].x() for b in self.balls])
            left_x = xs[0] - self.ball_radius
            right_x = xs[-1] + self.ball_radius
            
            painter.setPen(QPen(QColor(0, 100, 200), 2))
            
            # Левая граница
            painter.drawLine(int(left_x), self.row_y - 25, int(left_x), self.row_y - 45)
            # Правая граница
            painter.drawLine(int(right_x), self.row_y - 25, int(right_x), self.row_y - 45)
            # Линия между ними
            painter.drawLine(int(left_x), self.row_y - 35, int(right_x), self.row_y - 35)
            
            painter.setPen(QPen(QColor(0, 100, 200), 1))
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.drawText(int((left_x + right_x)/2 - 10), int(self.row_y - 40), "L")

    # Управление мышью (Drag & Drop)
    def mousePressEvent(self, event):
        p = event.position()
        for i, b in enumerate(self.balls):
            if (b['pos'] - p).manhattanLength() <= b['r'] + 6:
                self.drag_index = i
                return

    def mouseMoveEvent(self, event):
        if self.drag_index is None:
            return
        p = event.position()
        x = max(20, min(self.width() - 20, p.x()))
        self.balls[self.drag_index]['pos'].setX(x)
        self.balls[self.drag_index]['pos'].setY(self.row_y) # Фиксируем Y
        self.balls[self.drag_index]['target_x'] = x
        self.update()

    def mouseReleaseEvent(self, event):
        self.drag_index = None
        self.snap_to_row() # Авто-выравнивание

    def snap_to_row(self):
        """Схлопывание ряда шариков"""
        if len(self.balls) < 2:
            return
        
        # Сортируем по X
        self.balls.sort(key=lambda b: b['pos'].x())
        
        # Начальная позиция первого шарика
        start_x = self.balls[0]['pos'].x()
        
        # Ставим каждый следующий шарик вплотную
        diameter = self.ball_radius * 2
        for i, b in enumerate(self.balls):
            b['target_x'] = start_x + i * diameter

    def animate(self):
        """Плавная анимация движения"""
        changed = False
        for b in self.balls:
            tx = b.get('target_x', b['pos'].x())
            dx = tx - b['pos'].x()
            if abs(dx) > 0.5:
                b['pos'].setX(b['pos'].x() + dx * 0.2)
                changed = True
            else:
                b['pos'].setX(tx)
        if changed:
            self.update()

    def clear(self):
        self.balls = []
        self.update()

    def randomize(self):
        self._create_random_row()
        self.update()

    def get_measurements(self):
        """Получить истинные значения"""
        if len(self.balls) < 1:
            return 0, 0, 0
        
        self.balls.sort(key=lambda b: b['pos'].x())
        
        # Считаем в пикселях
        left_edge = self.balls[0]['pos'].x() - self.ball_radius
        right_edge = self.balls[-1]['pos'].x() + self.ball_radius
        
        px_dist = right_edge - left_edge
        
        # Переводим в мм
        mm_L = px_dist / self.ruler.px_per_mm
        N = len(self.balls)
        mm_d = mm_L / N
        return mm_L, N, mm_d

# ==========================================
# ГЛАВНОЕ ОКНО
# ==========================================
class Lab02App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №2: Катарный метод")
        self.resize(1100, 650)
        
        self.ruler_length = 250
        self.px_per_mm = 2.5
        
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # --- СЛЕВА: Визуализация ---
        left_group = QGroupBox("Визуальный стенд")
        left_layout = QVBoxLayout()
        
        self.ruler = RulerWidget(length_mm=self.ruler_length, px_per_mm=self.px_per_mm)
        self.balls_widget = BallsRowWidget(self.ruler)
        
        left_layout.addWidget(self.ruler)
        left_layout.addWidget(self.balls_widget)
        left_layout.addStretch(1)
        
        left_group.setLayout(left_layout)
        main_layout.addWidget(left_group, stretch=3)

        # --- СПРАВА: Панель управления ---
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, stretch=2)

        # 1. Задание
        task_group = QGroupBox("Задание")
        task_layout = QVBoxLayout()
        
        info = QLabel(
            "1. Выровняйте шарики в ряд (кнопка 'Выровнять').\n"
            "2. Измерьте общую длину ряда (L) по линейке.\n"
            "3. Посчитайте количество шариков (N).\n"
            "4. Рассчитайте диаметр одного шарика: d = L / N."
        )
        info.setWordWrap(True)
        task_layout.addWidget(info)
        task_group.setLayout(task_layout)
        right_panel.addWidget(task_group)

        # 2. Ввод данных
        input_group = QGroupBox("Ввод данных")
        input_layout = QVBoxLayout()
        
        self.inp_L = QLineEdit()
        self.inp_L.setPlaceholderText("Длина L (мм)")
        
        self.inp_N = QLineEdit()
        self.inp_N.setPlaceholderText("Количество N (шт)")
        
        self.inp_d = QLineEdit()
        self.inp_d.setPlaceholderText("Диаметр d (мм)")
        
        input_layout.addWidget(QLabel("Общая длина (L):"))
        input_layout.addWidget(self.inp_L)
        input_layout.addWidget(QLabel("Количество шариков (N):"))
        input_layout.addWidget(self.inp_N)
        input_layout.addWidget(QLabel("Диаметр (d = L/N):"))
        input_layout.addWidget(self.inp_d)
        
        input_group.setLayout(input_layout)
        right_panel.addWidget(input_group)

        # 3. Кнопки управления
        ctrl_group = QGroupBox("Управление")
        ctrl_layout = QVBoxLayout()
        
        self.btn_check = QPushButton("Проверить расчеты")
        self.btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 35px;")
        self.btn_check.clicked.connect(self.check_answer)
        
        h_layout = QHBoxLayout()
        self.btn_snap = QPushButton("Выровнять")
        self.btn_snap.clicked.connect(self.on_snap)
        self.btn_random = QPushButton("Новые шарики")
        self.btn_random.clicked.connect(self.on_random)
        
        h_layout.addWidget(self.btn_snap)
        h_layout.addWidget(self.btn_random)
        
        ctrl_layout.addWidget(self.btn_check)
        ctrl_layout.addLayout(h_layout)
        ctrl_group.setLayout(ctrl_layout)
        right_panel.addWidget(ctrl_group)

        # 4. Журнал
        res_group = QGroupBox("Журнал измерений")
        res_layout = QVBoxLayout()
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #f9f9f9; font-family: Consolas;")
        
        btn_copy = QPushButton("Копировать")
        btn_copy.clicked.connect(self.copy_log)
        
        res_layout.addWidget(self.txt_log)
        res_layout.addWidget(btn_copy)
        res_group.setLayout(res_layout)
        right_panel.addWidget(res_group, stretch=1)
        
        # 5. Выход
        btn_exit = QPushButton("Выход")
        btn_exit.setStyleSheet("background-color: #f44336; color: white;")
        btn_exit.clicked.connect(self.close)
        right_panel.addWidget(btn_exit)

    # --- ЛОГИКА ---
    def on_random(self):
        self.balls_widget.randomize()
        self.clear_inputs()
        self.txt_log.append("--- Новое задание сгенерировано ---")

    def on_snap(self):
        self.balls_widget.snap_to_row()

    def clear_inputs(self):
        self.inp_L.clear()
        self.inp_N.clear()
        self.inp_d.clear()

    def check_answer(self):
        # 1. Получение текста
        txt_L = self.inp_L.text().replace(',', '.')
        txt_N = self.inp_N.text()
        txt_d = self.inp_d.text().replace(',', '.')
        
        # 2. Валидация
        if not txt_L or not txt_N or not txt_d:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля!")
            return
            
        try:
            user_L = float(txt_L)
            user_N = int(txt_N)
            user_d = float(txt_d)
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Введите корректные числовые значения!")
            return

        # 3. Расчет правильных значений
        true_L, true_N, true_d = self.balls_widget.get_measurements()
        
        if true_N == 0:
            QMessageBox.warning(self, "Ошибка", "Шарики отсутствуют!")
            return

        # 4. Сравнение (с допуском погрешности)
        # L погрешность: 1.5 мм (погрешность глаза + экрана)
        is_L_ok = abs(user_L - true_L) <= 1.5 
        
        # N должно быть точным
        is_N_ok = (user_N == true_N)
        
        # d погрешность небольшая
        is_d_ok = abs(user_d - true_d) <= 0.2

        # 5. Вывод результата
        self.txt_log.append(f"Ввод: L={user_L}, N={user_N}, d={user_d}")
        
        all_ok = is_L_ok and is_N_ok and is_d_ok
        
        if all_ok:
            self.txt_log.append("<span style='color:green'><b>✅ ВЕРНО</b></span>")
        else:
            self.txt_log.append("<span style='color:red'><b>❌ ОШИБКА</b></span>")
            if not is_L_ok:
                self.txt_log.append(f"L неверно. Правильно: {true_L:.1f} мм")
            if not is_N_ok:
                self.txt_log.append(f"N неверно. Правильно: {true_N} шт.")
            if not is_d_ok:
                self.txt_log.append(f"d неверно. Правильно: {true_d:.2f} мм")
                
        self.txt_log.append("-" * 20)
        
        # Прокрутка вниз
        sb = self.txt_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def copy_log(self):
        self.txt_log.selectAll()
        self.txt_log.copy()
        cursor = self.txt_log.textCursor()
        cursor.clearSelection()
        self.txt_log.setTextCursor(cursor)
        QMessageBox.information(self, "Информация", "Журнал скопирован в буфер обмена!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = Lab02App()
    win.show()
    sys.exit(app.exec())