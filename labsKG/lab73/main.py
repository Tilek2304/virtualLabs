# lab03_scales_mass_only.py
# Требуется: pip install PySide6
import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF

class Weight:
    def __init__(self, mass, pos: QPointF):
        self.mass = mass
        self.pos = pos
        self.r = 12
        self.dragging = False
        self.on_plate = None  # 'left' or 'right' or None

class ScalesWidget(QFrame):
    """
    Рисует рычажные весы: опора, балка, чаши. Поддерживает перетаскивание гирь.
    Возвращает суммарные массы на левой и правой чашах.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(900, 420)
        self.center = QPointF(450, 180)  # позиция опоры (экранные координаты)
        self.beam_length = 360  # полная длина балки в пикселях
        self.beam_angle = 0.0
        self.target_angle = 0.0
        self.plate_radius = 40
        self.weights = []
        self.dragged = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        self._create_default_weights()

    def _create_default_weights(self):
        # создаём набор гирь разной массы, размещаем их справа от весов
        self.weights = []
        masses = [5, 10, 20, 50]  # граммы
        x0 = 720
        y0 = 80
        for i, m in enumerate(masses):
            w = Weight(mass=m, pos=QPointF(x0, y0 + i * 60))
            self.weights.append(w)
        # добавим одну неизвестную массу на левую чашу
        unknown = Weight(mass=random.choice([30,15, 25, 35,60,65,80,85,70,75]), pos=self.plate_center('left'))
        unknown.on_plate = 'left'
        self.weights.append(unknown)

    def plate_center(self, side):
        # возвращает экранные координаты центра чаши (чаши расположены ниже балки)
        angle = self.beam_angle
        if side == 'left':
            offset_x = -self.beam_length / 2
        else:
            offset_x = self.beam_length / 2
        ox, oy = offset_x, 0
        rx = ox * math.cos(angle) - oy * math.sin(angle)
        ry = ox * math.sin(angle) + oy * math.cos(angle)
        return QPointF(self.center.x() + rx, self.center.y() + ry + 80)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # фон
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        # опора
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QColor(200, 200, 200))
        base_rect = QRectF(self.center.x() - 12, self.center.y() + 40, 24, 80)
        painter.drawRoundedRect(base_rect, 6, 6)
        # балка
        painter.save()
        painter.translate(self.center)
        painter.rotate(math.degrees(self.beam_angle))
        painter.setPen(QPen(Qt.black, 3))
        painter.setBrush(QColor(220, 220, 240))
        beam_rect = QRectF(-self.beam_length/2, -8, self.beam_length, 16)
        painter.drawRoundedRect(beam_rect, 6, 6)
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(0, -12, 0, 12)
        painter.restore()
        # чаши
        left_center = self.plate_center('left')
        right_center = self.plate_center('right')
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QColor(240, 240, 240))
        painter.drawEllipse(left_center, self.plate_radius, 12)
        painter.drawEllipse(right_center, self.plate_radius, 12)
        # подвесы
        painter.setPen(QPen(Qt.black, 1))
        left_attach = self._beam_point(-self.beam_length/2)
        right_attach = self._beam_point(self.beam_length/2)
        painter.drawLine(left_attach, QPointF(left_center.x(), left_center.y() - 12))
        painter.drawLine(right_attach, QPointF(right_center.x(), right_center.y() - 12))
        # рисуем гири
        for wgt in self.weights:
            pos = wgt.pos
            # тень
            painter.setBrush(QColor(0, 0, 0, 40))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(pos.x()+3, pos.y()+4), wgt.r+3, wgt.r+3)
            # сама гиря
            painter.setBrush(QColor(200, 120, 60))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawEllipse(pos, wgt.r, wgt.r)
            # подпись массы
            painter.setPen(QPen(Qt.black, 1))
            painter.setFont(QFont("Sans", 9))
            painter.drawText(pos.x()-10, pos.y()+4, f"{wgt.mass}g")
            if wgt.on_plate:
                painter.setPen(QPen(QColor(40, 120, 200), 1))
                painter.drawEllipse(pos, wgt.r+2, wgt.r+2)

    def _beam_point(self, x_local):
        angle = self.beam_angle
        ox, oy = x_local, 0
        rx = ox * math.cos(angle) - oy * math.sin(angle)
        ry = ox * math.sin(angle) + oy * math.cos(angle)
        return QPointF(self.center.x() + rx, self.center.y() + ry)

    def mousePressEvent(self, event):
        p = event.position()
        for w in reversed(self.weights):
            if (w.pos - p).manhattanLength() <= w.r + 4:
                w.dragging = True
                self.dragged = w
                return

    def mouseMoveEvent(self, event):
        if not self.dragged:
            return
        p = event.position()
        x = max(20, min(self.width() - 20, p.x()))
        y = max(20, min(self.height() - 20, p.y()))
        self.dragged.pos = QPointF(x, y)
        self.dragged.on_plate = None
        self.update()

    def mouseReleaseEvent(self, event):
        if not self.dragged:
            return
        left_center = self.plate_center('left')
        right_center = self.plate_center('right')
        d_left = (self.dragged.pos - left_center).manhattanLength()
        d_right = (self.dragged.pos - right_center).manhattanLength()
        if d_left <= self.plate_radius + 8:
            self.dragged.pos = QPointF(left_center.x(), left_center.y() - 6)
            self.dragged.on_plate = 'left'
        elif d_right <= self.plate_radius + 8:
            self.dragged.pos = QPointF(right_center.x(), right_center.y() - 6)
            self.dragged.on_plate = 'right'
        else:
            self.dragged.on_plate = None
        self.dragged.dragging = False
        self.dragged = None
        # обновляем угол визуально, но без расчёта моментов — простая модель
        self._recompute_target_angle()
        self.update()

    def _recompute_target_angle(self):
        # простая визуальная модель: угол зависит от разницы сумм масс на чашах
        m_left = sum(w.mass for w in self.weights if w.on_plate == 'left')
        m_right = sum(w.mass for w in self.weights if w.on_plate == 'right')
        diff = m_right - m_left
        max_angle = math.radians(12)
        # масштабируем разницу для визуального эффекта
        self.target_angle = max(-max_angle, min(max_angle, diff / 200.0))

    def animate(self):
        da = self.target_angle - self.beam_angle
        if abs(da) > 0.0005:
            self.beam_angle += da * 0.18
            self.beam_angle += 0.002 * math.sin(self.target_angle * 10)
            self.update()

    def sum_masses(self):
        sum_left = sum(w.mass for w in self.weights if w.on_plate == 'left')
        sum_right = sum(w.mass for w in self.weights if w.on_plate == 'right')
        return sum_left, sum_right

    def reset(self):
        self._create_default_weights()
        self.beam_angle = 0.0
        self.target_angle = 0.0
        self.update()

class Lab03App(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Лабораторная №3 -> №3 Лабораториялык иш
        # Рычажные весы -> Рычагдуу тараза
        self.setWindowTitle("№3 Лабораториялык иш — Рычагдуу тараза")
        self.setMinimumSize(1000, 520)

        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 0)

        self.scales = ScalesWidget()
        left_layout.addWidget(self.scales)

        # Правая панель
        # КОТОРМО: Опыт: Рычажные весы -> Тажрыйба: Рычагдуу тараза
        lbl_title = QLabel("<b>Тажрыйба: Рычагдуу тараза</b>")
        right_layout.addWidget(lbl_title)

        # КОТОРМО: Инструкция
        self.lbl_info = QLabel(
            "Гирлерди таразанын табактарына сүйрөңүз. Максаты: белгисиз нерсенин массасын аныктоо.\n"
            "Белгисиз нерсенин массасын (г) гана киргизиңиз."
        )
        self.lbl_info.setWordWrap(True)
        right_layout.addWidget(self.lbl_info)

        # Показ текущих сумм масс на чашах (переменные оставим латиницей, понятно физикам)
        self.lbl_masses = QLabel("m_сол = 0 г\nm_оң = 0 г")
        right_layout.addWidget(self.lbl_masses)

        right_layout.addSpacing(6)
        # КОТОРМО: Ввод массы неизвестного тела -> Белгисиз нерсенин массасын киргизүү
        right_layout.addWidget(QLabel("<b>Белгисиз нерсенин массасын киргизүү</b>"))
        
        self.input_unknown = QLineEdit()
        # КОТОРМО: Введите массу... -> Белгисиз нерсенин массасын киргизиңиз (г)
        self.input_unknown.setPlaceholderText("Белгисиз нерсенин массасын киргизиңиз (г)")
        right_layout.addWidget(self.input_unknown)

        # Кнопки
        # КОТОРМО: Обновить значения -> Маанилерди жаңылоо
        btn_update = QPushButton("Маанилерди жаңылоо")
        btn_update.clicked.connect(self.update_values)
        
        # КОТОРМО: Проверить -> Текшерүү
        btn_check = QPushButton("Текшерүү")
        btn_check.clicked.connect(self.check_answer)
        
        # КОТОРМО: Показать правильную массу -> Туура массаны көрсөтүү
        btn_show = QPushButton("Туура массаны көрсөтүү")
        btn_show.clicked.connect(self.show_answer)
        
        # КОТОРМО: Сброс эксперимента -> Тажрыйбаны кайра баштоо
        btn_reset = QPushButton("Тажрыйбаны кайра баштоо")
        btn_reset.clicked.connect(self.reset_experiment)

        right_layout.addWidget(btn_update)
        right_layout.addWidget(btn_check)
        right_layout.addWidget(btn_show)
        right_layout.addWidget(btn_reset)

        self.lbl_result = QLabel("")
        self.lbl_result.setWordWrap(True)
        right_layout.addWidget(self.lbl_result)
        right_layout.addStretch(1)

        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_values)
        self.ui_timer.start(300)

    def update_values(self):
        m_left, m_right = self.scales.sum_masses()
        # КОТОРМО: m_left -> m_сол, m_right -> m_оң
        self.lbl_masses.setText(f"m_сол = {m_left:.1f} г\nm_оң = {m_right:.1f} г")

    def check_answer(self):
        try:
            user_unknown = float(self.input_unknown.text())
        except Exception:
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "Массанын сан маанисин киргизиңиз.")
            return
            
        m_left, _ = self.scales.sum_masses()
        # Поскольку неизвестный груз на левой чаше, его массу и ищем.
        # Но в коде unknown груз добавляется как 'left'.
        # Логика: мы уравновешиваем весы. Если весы в равновесии (угол ~ 0), то m_left = m_right.
        # В этой лабе мы просто просим ввести массу неизвестного тела.
        # В `_create_default_weights` неизвестное тело имеет массу и ставится на 'left'.
        # Значит, правильный ответ = масса того, что слева (включая неизвестное).
        # А стоп, `sum_masses` возвращает сумму ВСЕГО, что на чаше.
        # Если там только неизвестное тело, то m_left и есть искомая масса.
        
        tol = max(0.5, m_left * 0.05)
        
        if abs(user_unknown - m_left) <= tol:
            # КОТОРМО: ... рассчитана верно -> ... туура эсептелди
            self.lbl_result.setText("✅ Белгисиз нерсенин массасы туура эсептелди.")
        else:
            # КОТОРМО: Неверно... -> Туура эмес...
            self.lbl_result.setText(f"❌ Туура эмес. Сол табактагы жалпы масса: {m_left:.1f} г ( piela ±{tol:.2f} г).")

    def show_answer(self):
        m_left, _ = self.scales.sum_masses()
        self.input_unknown.setText(f"{m_left:.2f}")
        # КОТОРМО: Показана правильная масса -> Туура масса көрсөтүлдү
        self.lbl_result.setText("Туура масса көрсөтүлдү.")

    def reset_experiment(self):
        self.scales.reset()
        self.input_unknown.clear()
        # КОТОРМО: Эксперимент сброшен -> Тажрыйба башынан башталды
        self.lbl_result.setText("Тажрыйба башынан башталды.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Lab03App()
    win.show()
    sys.exit(app.exec())
