# lab01_menzurka_animated.py
# Требуется: pip install PySide6
import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QHBoxLayout, QFrame, QSizePolicy
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PySide6.QtCore import Qt, QTimer, QRectF

class MenzurkaWidget(QFrame):
    """
    Рисует мензурку с делениями, подписями справа и анимированным уровнем жидкости.
    Параметры: полный объём (мл), объём жидкости (мл), число делений.
    """
    def __init__(self, total_volume, liquid_volume, divisions, parent=None):
        super().__init__(parent)
        self.total_volume = total_volume
        self.base_liquid = liquid_volume
        self.divisions = divisions

        self.setMinimumSize(220, 420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Анимация: фаза и амплитуда (в пикселях)
        self.phase = 0.0
        self.amp_px = 3.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(40)  # ~25 FPS

    def on_timer(self):
        # Небольшая синусоидальная колебательная анимация уровня жидкости
        self.phase += 0.12
        if self.phase > 2 * math.pi:
            self.phase -= 2 * math.pi
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin_x = int(w * 0.12)
        margin_y = int(h * 0.06)

        cyl_w = int(w * 0.36)
        cyl_h = int(h * 0.84)
        cyl_x = margin_x
        cyl_y = margin_y

        # Рисуем корпус мензурки (прозрачное стекло)
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        rect = QRectF(cyl_x, cyl_y, cyl_w, cyl_h)
        painter.drawRoundedRect(rect, 6, 6)

        # Внутренний отступ (толщина стенки)
        inner_x = cyl_x + 6
        inner_w = cyl_w - 12
        inner_y = cyl_y + 6
        inner_h = cyl_h - 12

        # Вычисляем текущую высоту жидкости в пикселях с анимацией
        base_height_px = inner_h * (self.base_liquid / self.total_volume)
        anim_offset = self.amp_px * math.sin(self.phase)
        liquid_height_px = max(0.0, min(inner_h, base_height_px + anim_offset))
        liquid_top_y = inner_y + inner_h - liquid_height_px

        # Рисуем жидкость с "мениском" (легкая волна)
        path = QPainterPath()
        left = inner_x
        right = inner_x + inner_w
        bottom = inner_y + inner_h
        # волнистая верхняя граница
        wave_ampl = 4.0  # пиксели для волны
        wave_len = inner_w / 3.0
        path.moveTo(left, bottom)
        path.lineTo(left, liquid_top_y + wave_ampl * math.sin(0))
        # создаём простую синусоиду по ширине
        steps = 40
        for i in range(steps + 1):
            t = i / steps
            x = left + t * inner_w
            phase = self.phase + t * 2 * math.pi
            y = liquid_top_y + math.sin(phase) * (wave_ampl * (1 - abs(2*t-1)))
            path.lineTo(x, y)
        path.lineTo(right, bottom)
        path.closeSubpath()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(100, 150, 255, 220))
        painter.drawPath(path)

        # Рисуем горизонтальную линию уровня (чуть темнее)
        painter.setPen(QPen(QColor(40, 80, 160, 200), 1))
        painter.drawLine(left, liquid_top_y, right, liquid_top_y)

        # Рисуем деления и подписи справа от мензурки
        painter.setPen(QPen(Qt.black, 1))
        font = QFont("Sans", max(8, int(w * 0.03)))
        painter.setFont(font)
        for i in range(self.divisions + 1):
            # i=0 - низ, i=divisions - верх
            t = i / self.divisions
            y_tick = inner_y + inner_h - t * inner_h
            # длинные линии через каждые 1 деление (все одинаковые здесь)
            painter.drawLine(inner_x - 6, y_tick, inner_x + inner_w + 6, y_tick)
            # подпись справа: значение в мл
            value = int(round(t * self.total_volume))
            var = i%10
            if var == 0:
                text = f"{value}"
            else:
                text = f" "
            # подпись чуть правее корпуса
            
            painter.drawText(inner_x + inner_w + 12, y_tick + 4, text)

        # Рисуем шкалу нулевой подписи внизу (0)
        painter.setPen(QPen(Qt.black, 1))
        painter.drawText(inner_x - 6, inner_y + inner_h + 18, "0")

        # Рисуем основание мензурки (подставка)
        base_w = int(cyl_w * 0.9)
        base_x = cyl_x + (cyl_w - base_w) // 2
        base_y = cyl_y + cyl_h + 6
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QColor(220, 220, 220))
        painter.drawRoundedRect(base_x, base_y, base_w, 12, 4, 4)

        # Текстовая подпись "мл" слева от верхней части
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Sans", max(9, int(w * 0.035)), QFont.Bold))
        painter.drawText(cyl_x, cyl_y - 6, "мл")

class Lab01App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная №1 — Цена деления мензурки (анимированная)")
        self.setMinimumSize(760, 520)

        # Генерация случайных параметров
        self.V_total = random.choice([100, 500, 1000])   # полный объём мензурки (мл)
        # self.V_total = random.randrange(100, 1000, 100)   # полный объём мензурки (мл)
        self.N = random.choice([50])       # количество делений
        self.V_liquid = random.randrange(self.N, self.V_total,50)  # реальный объём жидкости (мл)
        self.price = self.V_total / self.N

        # Основной layout: слева menzurka, справа панель с параметрами и вводом
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Виджет мензурки
        self.menzurka_widget = MenzurkaWidget(self.V_total, self.V_liquid, self.N)
        main_layout.addWidget(self.menzurka_widget, 1)

        # Правая панель
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)
        main_layout.addLayout(right_panel, 0)

        # Информационный блок (параметры menzurka)
        info_frame = QFrame()
        info_layout = QVBoxLayout()
        info_frame.setLayout(info_layout)
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setFixedWidth(300)

        lbl_title = QLabel("<b>Параметры мензурки</b>")
        lbl_title.setAlignment(Qt.AlignLeft)
        info_layout.addWidget(lbl_title)

        # Показываем V_total и N (объём жидкости скрыт)
        self.lbl_total = QLabel(f"Полный объём: <b>{self.V_total} мл</b>")
        self.lbl_divs = QLabel(f"Число делений: <b>{self.N}</b>")
        self.lbl_hint = QLabel("Уровень жидкости показан на шкале.\nВычислите цену деления и объём.")
        self.lbl_hint.setWordWrap(True)

        info_layout.addWidget(self.lbl_total)
        info_layout.addWidget(self.lbl_divs)
        info_layout.addWidget(self.lbl_hint)
        info_layout.addStretch(1)

        right_panel.addWidget(info_frame)

        # Поля ввода ответов
        input_frame = QFrame()
        input_layout = QVBoxLayout()
        input_frame.setLayout(input_layout)
        input_frame.setFixedWidth(300)

        lbl_ans = QLabel("<b>Ввод ответов</b>")
        input_layout.addWidget(lbl_ans)

        self.input_price = QLineEdit()
        self.input_price.setPlaceholderText("Введите цену деления (мл), например 63.0")
        input_layout.addWidget(self.input_price)

        self.input_volume = QLineEdit()
        self.input_volume.setPlaceholderText("Введите объём жидкости (мл)")
        input_layout.addWidget(self.input_volume)

        # Кнопки: Проверить и Показать ответ
        btn_layout = QHBoxLayout()
        self.btn_check = QPushButton("Проверить")
        self.btn_check.clicked.connect(self.check_answers)
        self.btn_show = QPushButton("Показать ответ")
        self.btn_show.clicked.connect(self.show_answer)
        btn_layout.addWidget(self.btn_check)
        btn_layout.addWidget(self.btn_show)
        input_layout.addLayout(btn_layout)

        # Результат
        self.lbl_result = QLabel("")
        self.lbl_result.setWordWrap(True)
        input_layout.addWidget(self.lbl_result)
        input_layout.addStretch(1)

        right_panel.addWidget(input_frame)
        right_panel.addStretch(1)

    def check_answers(self):
        # Проверка введённых значений
        try:
            user_price = float(self.input_price.text())
            user_volume = float(self.input_volume.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения в оба поля.")
            return

        # Допуски: цена деления — 0.5% или 0.1 мл, объём — 1 мл
        tol_price = max(0.1, abs(self.price) * 0.005)
        tol_volume = 1.0

        ok_price = abs(user_price - self.price) <= tol_price
        ok_volume = abs(user_volume - self.V_liquid) <= tol_volume

        msg_lines = []
        if ok_price:
            msg_lines.append("✅ Цена деления рассчитана верно.")
        else:
            msg_lines.append(f"❌ Неверно. Правильная цена деления: {self.price:.2f} мл (допуск ±{tol_price:.2f} мл).")

        if ok_volume:
            msg_lines.append("✅ Объём жидкости рассчитан верно.")
        else:
            msg_lines.append(f"❌ Неверно. Правильный объём: {self.V_liquid} мл (допуск ±{tol_volume:.1f} мл).")

        self.lbl_result.setText("\n".join(msg_lines))

    def show_answer(self):
        # Показываем правильные ответы
        self.lbl_result.setText(
            f"Правильная цена деления: {self.price:.2f} мл\n"
            f"Правильный объём жидкости: {self.V_liquid} мл"
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Lab01App()
    win.show()
    sys.exit(app.exec())
