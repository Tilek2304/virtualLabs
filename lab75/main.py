# lab_density.py
# Требуется: pip install PySide6
import sys
import random
import math
from statistics import mean, pstdev
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF

# ---------------------------
# Виджет мензурки
# ---------------------------
class MenzurkaWidget(QFrame):
    def __init__(self, total_volume, liquid_volume, divisions, body_volume, parent=None):
        super().__init__(parent)
        self.total_volume = total_volume
        self.V1 = liquid_volume
        self.V_body = body_volume
        self.divisions = divisions

        self.setMinimumSize(320, 420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(30)

        # animation state: 0 up, 1 lowering, 2 down, 3 raising
        self.state = 0
        self.anim_t = 0.0
        self.anim_speed = 0.02

    def on_timer(self):
        self.phase += 0.12
        if self.phase > 2 * math.pi:
            self.phase -= 2 * math.pi
        if self.state in (1, 3):
            self.anim_t += self.anim_speed if self.state == 1 else -self.anim_speed
            if self.anim_t >= 1.0:
                self.anim_t = 1.0
                self.state = 2
            if self.anim_t <= 0.0:
                self.anim_t = 0.0
                self.state = 0
        self.update()

    def start_lower(self):
        if self.state == 0:
            self.state = 1
            self.anim_t = 0.0

    def start_raise(self):
        if self.state in (1, 2):
            self.state = 3

    def set_auto(self):
        if self.state in (0, 3):
            self.start_lower()
        elif self.state in (1, 2):
            self.start_raise()

    def immerse_now(self):
        # немедленно погрузить тело: установить итоговое состояние
        self.state = 2
        self.anim_t = 1.0
        self.update()

    def current_liquid_volume(self):
        V2 = self.V1 + self.V_body
        t = self.anim_t if self.state in (1,2,3) else 0.0
        return self.V1 + (V2 - self.V1) * t

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width(); h = self.height()
        margin = 18
        cyl_w = int(w * 0.36)
        cyl_h = int(h * 0.78)
        cyl_x = margin; cyl_y = margin

        # outer glass
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(cyl_x, cyl_y, cyl_w, cyl_h, 8, 8)

        inner_x = cyl_x + 8
        inner_w = cyl_w - 16
        inner_y = cyl_y + 8
        inner_h = cyl_h - 16

        V_current = self.current_liquid_volume()
        liquid_height = inner_h * (V_current / self.total_volume)
        liquid_y = inner_y + inner_h - liquid_height

        # liquid path with wave
        path = QPainterPath()
        left = inner_x; right = inner_x + inner_w; bottom = inner_y + inner_h
        steps = 60
        wave_ampl = 3.0
        path.moveTo(left, bottom)
        for i in range(steps + 1):
            t = i / steps
            x = left + t * inner_w
            phase = self.phase + t * 2 * math.pi
            y = liquid_y + math.sin(phase) * (wave_ampl * (1 - abs(2*t-1)))
            path.lineTo(x, y)
        path.lineTo(right, bottom)
        path.closeSubpath()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(100,150,255,220))
        painter.drawPath(path)

        painter.setPen(QPen(QColor(40,80,160,200), 1))
        painter.drawLine(left, liquid_y, right, liquid_y)

        # divisions (smaller font)
        painter.setPen(QPen(Qt.black, 1))
        font_size = max(6, int(w * 0.014))
        painter.setFont(QFont("Sans", font_size))
        for i in range(self.divisions + 1):
            t = i / self.divisions
            y_tick = inner_y + inner_h - t * inner_h
            if self.divisions >= 10 and i % (self.divisions // 10) == 0:
                tick_len = 12
            elif self.divisions >= 5 and i % (self.divisions // 5) == 0:
                tick_len = 8
            else:
                tick_len = 5
            painter.drawLine(inner_x - tick_len, y_tick, inner_x, y_tick)
            value = int(round(t * self.total_volume))
            painter.drawText(inner_x + inner_w + 10, y_tick + 4, f"{value}")

        # body on thread centered
        body_radius = min(36, int(inner_w * 0.5))
        top_anchor_x = inner_x + inner_w / 2
        top_anchor_y = inner_y - 36
        liquid_top_y = liquid_y
        top_y = top_anchor_y + 18
        bottom_y = liquid_top_y + body_radius * 0.6
        t = self.anim_t if self.state in (1,2,3) else 0.0
        body_cy = top_y + (bottom_y - top_y) * t
        body_cx = top_anchor_x
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(top_anchor_x, top_anchor_y, body_cx, body_cy - body_radius)
        painter.setBrush(QColor(180,80,80))
        painter.setPen(QPen(Qt.black,1))
        painter.drawEllipse(QPointF(body_cx, body_cy), body_radius, body_radius)
        painter.setPen(QPen(Qt.white,1))
        painter.setFont(QFont("Sans", 9, QFont.Bold))
        painter.drawText(body_cx - 18, body_cy + 4, "тело")

        # info panel
        info_x = inner_x + inner_w + 12
        info_y = inner_y + 6
        painter.setPen(QPen(Qt.black,1))
        painter.setFont(QFont("Sans", 10))
        painter.drawText(info_x, info_y + 0, f"Полный объём: {self.total_volume} мл")
        painter.drawText(info_x, info_y + 18, f"Делений: {self.divisions}")
        painter.drawText(info_x, info_y + 36, f"V1 (показан): {self.V1:.1f} мл")
        if self.state in (1,2,3) or self.anim_t > 0:
            V2 = self.V1 + self.V_body
            painter.drawText(info_x, info_y + 54, f"V2 (итог): {V2:.1f} мл")
        else:
            painter.drawText(info_x, info_y + 54, f"V2 (итог): —")

# ---------------------------
# Простейшие весы с перетаскиванием гирь
# ---------------------------
class Weight:
    def __init__(self, mass, pos):
        self.mass = mass
        self.pos = QPointF(pos)
        self.r = 12
        self.dragging = False
        self.on_plate = None  # 'left' or 'right' or None

class ScalesWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 260)
        self.center = QPointF(160, 80)
        self.beam_length = 220
        self.beam_angle = 0.0
        self.target_angle = 0.0
        self.plate_radius = 28
        self.weights = []
        self.dragged = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        self._create_default_weights()

    def _create_default_weights(self):
        self.weights = []
        masses = [1,2,5,10,20,50]
        x0 = 260; y0 = 20
        for i,m in enumerate(masses):
            w = Weight(mass=m, pos=QPointF(x0, y0 + i*34))
            self.weights.append(w)
        # unknown mass on left plate
        unknown_mass = random.choice([12,18,24,30,36])
        unk = Weight(mass=unknown_mass, pos=self.plate_center('left'))
        unk.on_plate = 'left'
        self.weights.append(unk)

    def plate_center(self, side):
        angle = self.beam_angle
        if side == 'left':
            offset_x = -self.beam_length/2
        else:
            offset_x = self.beam_length/2
        ox, oy = offset_x, 0
        rx = ox * math.cos(angle) - oy * math.sin(angle)
        ry = ox * math.sin(angle) + oy * math.cos(angle)
        return QPointF(self.center.x() + rx, self.center.y() + ry + 80)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(250,250,250))
        painter.setPen(QPen(Qt.black,2))
        painter.setBrush(QColor(200,200,200))
        base_rect = QRectF(self.center.x()-10, self.center.y()+40, 20, 60)
        painter.drawRoundedRect(base_rect,4,4)
        painter.save()
        painter.translate(self.center)
        painter.rotate(math.degrees(self.beam_angle))
        painter.setPen(QPen(Qt.black,3))
        painter.setBrush(QColor(220,220,240))
        beam_rect = QRectF(-self.beam_length/2, -6, self.beam_length, 12)
        painter.drawRoundedRect(beam_rect,6,6)
        painter.setPen(QPen(Qt.black,1))
        painter.drawLine(0,-10,0,10)
        painter.restore()
        left_center = self.plate_center('left')
        right_center = self.plate_center('right')
        painter.setPen(QPen(Qt.black,2))
        painter.setBrush(QColor(240,240,240))
        painter.drawEllipse(left_center, self.plate_radius, 10)
        painter.drawEllipse(right_center, self.plate_radius, 10)
        left_attach = self._beam_point(-self.beam_length/2)
        right_attach = self._beam_point(self.beam_length/2)
        painter.setPen(QPen(Qt.black,1))
        painter.drawLine(left_attach, QPointF(left_center.x(), left_center.y()-10))
        painter.drawLine(right_attach, QPointF(right_center.x(), right_center.y()-10))
        for w in self.weights:
            pos = w.pos
            painter.setBrush(QColor(0,0,0,30))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(pos.x()+2,pos.y()+3), w.r+3, w.r+3)
            painter.setBrush(QColor(200,120,60))
            painter.setPen(QPen(Qt.black,1))
            painter.drawEllipse(pos, w.r, w.r)
            painter.setPen(QPen(Qt.black,1))
            painter.setFont(QFont("Sans",9))
            painter.drawText(pos.x()-10, pos.y()+4, f"{w.mass}g")
            if w.on_plate:
                painter.setPen(QPen(QColor(40,120,200),1))
                painter.drawEllipse(pos, w.r+2, w.r+2)

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
        x = max(10, min(self.width()-10, p.x()))
        y = max(10, min(self.height()-10, p.y()))
        self.dragged.pos = QPointF(x,y)
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
            self.dragged.pos = QPointF(left_center.x(), left_center.y()-6)
            self.dragged.on_plate = 'left'
        elif d_right <= self.plate_radius + 8:
            self.dragged.pos = QPointF(right_center.x(), right_center.y()-6)
            self.dragged.on_plate = 'right'
        else:
            self.dragged.on_plate = None
        self.dragged.dragging = False
        self.dragged = None
        self._recompute_target_angle()
        self.update()

    def _recompute_target_angle(self):
        m_left = sum(w.mass for w in self.weights if w.on_plate == 'left')
        m_right = sum(w.mass for w in self.weights if w.on_plate == 'right')
        diff = m_right - m_left
        max_angle = math.radians(10)
        self.target_angle = max(-max_angle, min(max_angle, diff / 120.0))

    def animate(self):
        da = self.target_angle - self.beam_angle
        if abs(da) > 0.0005:
            self.beam_angle += da * 0.18
            self.beam_angle += 0.001 * math.sin(self.target_angle * 10)
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

# ---------------------------
# Главное приложение
# ---------------------------
class LabDensityApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная — Плотность твёрдых тел")
        # увеличиваем минимальный размер окна в 1.5 раза
        self.setMinimumSize(1650, 900)

        self._generate_experiment()

        main_layout = QHBoxLayout(self)
        left_col = QVBoxLayout()
        right_col = QVBoxLayout()
        main_layout.addLayout(left_col, 1)
        main_layout.addLayout(right_col, 0)

        # визуализация: мензурка и весы
        self.menzurka = MenzurkaWidget(
            total_volume=self.V_total,
            liquid_volume=self.V1,
            divisions=self.N,
            body_volume=self.V_body
        )
        self.scales = ScalesWidget()

        left_col.addWidget(self.menzurka, 2)
        left_col.addWidget(self.scales, 1)

        # правая панель управления
        right_col.addWidget(QLabel("<b>Плотность твёрдых тел</b>"))
        info = QLabel("Определите плотность тела: измерьте массу m на весах и объём V по мензурке.\n"
                      "Вводите m, V и вычисленную плотность ρ = m / V (г/мл).")
        info.setWordWrap(True)
        right_col.addWidget(info)

        # показ текущих измерений
        self.lbl_current = QLabel("m_left = 0 g\nV_current = 0.0 мл")
        right_col.addWidget(self.lbl_current)

        # поля ввода
        right_col.addSpacing(6)
        right_col.addWidget(QLabel("<b>Ввод результатов</b>"))
        self.input_m = QLineEdit(); self.input_m.setPlaceholderText("Введите m, г")
        self.input_V = QLineEdit(); self.input_V.setPlaceholderText("Введите V, мл")
        self.input_rho = QLineEdit(); self.input_rho.setPlaceholderText("Введите ρ = m / V, г/мл")
        right_col.addWidget(self.input_m)
        right_col.addWidget(self.input_V)
        right_col.addWidget(self.input_rho)

        # кнопки
        btn_update = QPushButton("Обновить значения")
        btn_update.clicked.connect(self.update_values)
        btn_check = QPushButton("Проверить")
        btn_check.clicked.connect(self.check_answers)
        btn_show = QPushButton("Показать ответ")
        btn_show.clicked.connect(self.show_answer)
        btn_add = QPushButton("Добавить в таблицу")
        btn_add.clicked.connect(self.add_to_table)
        btn_reset = QPushButton("Сброс эксперимента")
        btn_reset.clicked.connect(self.reset_experiment)
        btn_random = QPushButton("Случайный эксперимент")
        btn_random.clicked.connect(self.random_experiment)
        # новая кнопка: Погрузить тело
        btn_immerse = QPushButton("Погрузить тело")
        btn_immerse.clicked.connect(self.immerse_body_now)

        right_col.addWidget(btn_update)
        right_col.addWidget(btn_check)
        right_col.addWidget(btn_show)
        right_col.addWidget(btn_add)
        right_col.addWidget(btn_random)
        right_col.addWidget(btn_reset)
        right_col.addWidget(btn_immerse)

        # результат
        self.lbl_result = QLabel("")
        self.lbl_result.setWordWrap(True)
        right_col.addWidget(self.lbl_result)

        # таблица измерений
        right_col.addSpacing(8)
        right_col.addWidget(QLabel("<b>Таблица измерений</b>"))
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["m, г", "V, мл", "ρ, г/мл"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_col.addWidget(self.table)

        # статистика
        self.lbl_stats = QLabel("Средняя ρ: —    σ: —")
        right_col.addWidget(self.lbl_stats)
        right_col.addStretch(1)

        # таймер обновления
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_values)
        self.ui_timer.start(250)

    def _generate_experiment(self):
        self.V_total = random.randint(200, 800)
        self.N = random.choice([10,20,50])
        self.V_body = random.randint(5, max(5, int(self.V_total*0.2)))
        self.V1 = random.randint(10, max(20, self.V_total - self.V_body - 10))

    def update_values(self):
        m_left, m_right = self.scales.sum_masses()
        V_current = self.menzurka.current_liquid_volume()
        self.lbl_current.setText(f"m_left = {m_left:.1f} g\nV_current = {V_current:.2f} мл")

    def check_answers(self):
        try:
            user_m = float(self.input_m.text())
            user_V = float(self.input_V.text())
            user_rho = float(self.input_rho.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения в поля m, V, ρ.")
            return
        true_m, _ = self.scales.sum_masses()
        true_V = float(self.menzurka.current_liquid_volume())
        true_rho = true_m / true_V if true_V > 0 else 0.0

        tol_m = max(0.5, true_m * 0.02)
        tol_V = max(0.5, self.menzurka.total_volume / self.menzurka.divisions)
        tol_rho = max(0.01, true_rho * 0.03)

        ok_m = abs(user_m - true_m) <= tol_m
        ok_V = abs(user_V - true_V) <= tol_V
        ok_rho = abs(user_rho - true_rho) <= tol_rho

        lines = []
        if ok_m:
            lines.append("✅ m рассчитано верно.")
        else:
            lines.append(f"❌ m неверно. Правильная m: {true_m:.2f} г (допуск ±{tol_m:.2f} г).")
        if ok_V:
            lines.append("✅ V рассчитано верно.")
        else:
            lines.append(f"❌ V неверно. Правильное V: {true_V:.2f} мл (допуск ±{tol_V:.2f} мл).")
        if ok_rho:
            lines.append("✅ ρ рассчитана верно.")
        else:
            lines.append(f"❌ ρ неверно. Правильная ρ: {true_rho:.3f} г/мл (допуск ±{tol_rho:.3f}).")
        self.lbl_result.setText("\n".join(lines))

    def show_answer(self):
        true_m, _ = self.scales.sum_masses()
        true_V = float(self.menzurka.current_liquid_volume())
        true_rho = true_m / true_V if true_V > 0 else 0.0
        self.input_m.setText(f"{true_m:.2f}")
        self.input_V.setText(f"{true_V:.2f}")
        self.input_rho.setText(f"{true_rho:.4f}")
        self.lbl_result.setText("Показаны правильные значения.")

    def add_to_table(self):
        try:
            m = float(self.input_m.text())
            V = float(self.input_V.text())
            rho = float(self.input_rho.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения перед добавлением.")
            return
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(f"{m:.2f}"))
        self.table.setItem(row, 1, QTableWidgetItem(f"{V:.2f}"))
        self.table.setItem(row, 2, QTableWidgetItem(f"{rho:.4f}"))
        self._update_stats()

    def _update_stats(self):
        vals = []
        for r in range(self.table.rowCount()):
            try:
                rho = float(self.table.item(r,2).text())
                vals.append(rho)
            except Exception:
                pass
        if vals:
            avg = mean(vals)
            sigma = pstdev(vals) if len(vals) > 1 else 0.0
            self.lbl_stats.setText(f"Средняя ρ: {avg:.4f} г/мл    σ: {sigma:.4f}")
        else:
            self.lbl_stats.setText("Средняя ρ: —    σ: —")

    def reset_experiment(self):
        self.menzurka.state = 0
        self.menzurka.anim_t = 0.0
        self.scales.reset()
        self.input_m.clear(); self.input_V.clear(); self.input_rho.clear()
        self.lbl_result.setText("")
        self.table.setRowCount(0)
        self.lbl_stats.setText("Средняя ρ: —    σ: —")
        self.update_values()

    def random_experiment(self):
        self._generate_experiment()
        # recreate widgets with new params
        parent_layout = self.layout().itemAt(0).layout()
        left_layout = parent_layout.itemAt(0).layout()
        while left_layout.count():
            item = left_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.menzurka = MenzurkaWidget(
            total_volume=self.V_total,
            liquid_volume=self.V1,
            divisions=self.N,
            body_volume=self.V_body
        )
        self.scales = ScalesWidget()
        left_layout.addWidget(self.menzurka, 2)
        left_layout.addWidget(self.scales, 1)
        self.reset_experiment()

    def immerse_body_now(self):
        # вызывается по кнопке "Погрузить тело"
        self.menzurka.immerse_now()
        self.update_values()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabDensityApp()
    win.show()
    sys.exit(app.exec())
