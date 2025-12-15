# lab04_displacement.py
# Требуется: pip install PySide6
import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF

class MenzurkaWidget(QFrame):
    """
    Рисует мензурку с делениями, подписями справа и анимированным уровнем жидкости.
    Поддерживает опускание/подъём тела на нитке и плавную анимацию мениска.
    """
    def __init__(self, total_volume, liquid_volume, divisions, body_volume, parent=None):
        super().__init__(parent)
        self.total_volume = total_volume
        self.V1 = liquid_volume
        self.V_body = body_volume
        self.divisions = divisions

        self.setMinimumSize(300, 520)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Анимация уровня
        self.phase = 0.0
        self.amp_px = 3.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(30)  # ~33 FPS

        # Animation state: 0 = body up, 1 = lowering, 2 = body down, 3 = raising
        self.state = 0
        self.anim_t = 0.0  # interpolation 0..1
        self.anim_speed = 0.02

        # Precompute pixel mapping later in paintEvent
        self._cached_inner = None

    def on_timer(self):
        self.phase += 0.12
        if self.phase > 2 * math.pi:
            self.phase -= 2 * math.pi

        # animate lowering/raising
        if self.state in (1, 3):
            self.anim_t += self.anim_speed if self.state == 1 else -self.anim_speed
            if self.anim_t >= 1.0:
                self.anim_t = 1.0
                self.state = 2  # reached bottom
            if self.anim_t <= 0.0:
                self.anim_t = 0.0
                self.state = 0  # reached top
        self.update()

    def start_lower(self):
        if self.state == 0:
            self.state = 1
            self.anim_t = 0.0

    def start_raise(self):
        if self.state in (1, 2):
            self.state = 3
            if self.anim_t <= 0.0:
                self.anim_t = 0.0

    def set_auto(self):
        # toggle auto: if up -> lower; if down -> raise
        if self.state in (0, 3):
            self.start_lower()
        elif self.state in (1, 2):
            self.start_raise()

    def current_liquid_volume(self):
        # interpolate between V1 and V2 based on anim_t
        V2 = self.V1 + self.V_body
        t = self.anim_t if self.state in (1,2,3) else 0.0
        # if raising, anim_t decreases; current t already reflects that
        return self.V1 + (V2 - self.V1) * t

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 24
        cyl_w = int(w * 0.28)
        cyl_h = int(h * 0.78)
        cyl_x = margin
        cyl_y = margin

        # Draw outer glass
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(cyl_x, cyl_y, cyl_w, cyl_h, 8, 8)

        # Inner area (account for glass thickness)
        inner_x = cyl_x + 8
        inner_w = cyl_w - 16
        inner_y = cyl_y + 8
        inner_h = cyl_h - 16

        # Cache inner geometry for mapping
        self._cached_inner = (inner_x, inner_y, inner_w, inner_h)

        # Compute current liquid height in pixels
        V_current = self.current_liquid_volume()
        liquid_height = inner_h * (V_current / self.total_volume)
        liquid_y = inner_y + inner_h - liquid_height

        # Draw liquid with wavy meniscus
        path = QPainterPath()
        left = inner_x
        right = inner_x + inner_w
        bottom = inner_y + inner_h
        wave_ampl = 4.0
        steps = 60
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
        painter.setBrush(QColor(100, 150, 255, 220))
        painter.drawPath(path)

        # Draw horizontal level line
        painter.setPen(QPen(QColor(40, 80, 160, 200), 1))
        painter.drawLine(left, liquid_y, right, liquid_y)

        # Draw divisions and numeric labels to the right
        painter.setPen(QPen(Qt.black, 1))
        # уменьшенный шрифт для подписей делений (в 2 раза меньше)
        font_size = max(6, int(w * 0.015))  # раньше было int(w * 0.03)
        font = QFont("Sans", font_size)
        painter.setFont(font)
        for i in range(self.divisions + 1):
            t = i / self.divisions
            y_tick = inner_y + inner_h - t * inner_h
            # tick length varies
            if self.divisions >= 10 and i % (self.divisions // 10) == 0:
                tick_len = 12
            elif self.divisions >= 5 and i % (self.divisions // 5) == 0:
                tick_len = 8
            else:
                tick_len = 5
            painter.drawLine(inner_x - tick_len, y_tick, inner_x, y_tick)
            # numeric label on right (меньший шрифт)
            value = int(round(t * self.total_volume))
            painter.drawText(inner_x + inner_w + 12, y_tick + 4, f"{value}")

        # Draw base
        base_w = int(cyl_w * 0.9)
        base_x = cyl_x + (cyl_w - base_w) // 2
        base_y = cyl_y + cyl_h + 8
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QColor(220, 220, 220))
        painter.drawRoundedRect(base_x, base_y, base_w, 12, 4, 4)

        # Draw textual info above menzurka
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Sans", max(9, int(w * 0.035)), QFont.Bold))
        painter.drawText(cyl_x, cyl_y - 8, "мл")

        # Draw body on a thread directly over the menzurka (по центру внутренней области)
        body_radius = min(40, int(inner_w * 0.6))
        # anchor point above the menzurka (по центру)
        top_anchor_x = inner_x + inner_w / 2
        top_anchor_y = inner_y - 40
        # compute vertical position of body: when anim_t=0 -> above liquid; anim_t=1 -> submerged center at liquid mid
        V_current = self.current_liquid_volume()
        liquid_height_px = inner_h * (V_current / self.total_volume)
        liquid_top_y = inner_y + inner_h - liquid_height_px
        # define top and bottom positions
        top_y = top_anchor_y + 20
        bottom_y = liquid_top_y + body_radius * 0.6
        # interpolation by anim_t
        t = self.anim_t if self.state in (1,2,3) else 0.0
        body_cy = top_y + (bottom_y - top_y) * t
        body_cx = top_anchor_x  # центр над мензуркой
        # draw thread
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(top_anchor_x, top_anchor_y, body_cx, body_cy - body_radius)
        # draw body (circle) — рисуем после жидкости, чтобы тело накладывалось на мензурку
        painter.setBrush(QColor(180, 80, 80))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawEllipse(QPointF(body_cx, body_cy), body_radius, body_radius)
        # label body volume (hidden from student)
# КОТОРМО: тело -> нерсе
        painter.setPen(QPen(Qt.white, 1))
        painter.setFont(QFont("Sans", 9, QFont.Bold))
        painter.drawText(body_cx - 20, body_cy + 4, "нерсе")

        # Draw small panel with V_total, N, V1 (shown), V2 hidden until body down
        info_x = inner_x + inner_w + 12
        info_y = inner_y + inner_h * 0.02
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Sans", 10))
        # КОТОРМО: Полный объём -> Толук көлөмү
        painter.drawText(info_x, info_y + 0, f"Толук көлөмү: {self.total_volume} мл")
        # КОТОРМО: Делений -> Бөлүктөр
        painter.drawText(info_x, info_y + 20, f"Бөлүктөр: {self.divisions}")
        # КОТОРМО: V1 (показан) -> V1 (көрсөтүлдү)
        painter.drawText(info_x, info_y + 40, f"V1 (көрсөтүлдү): {self.V1:.1f} мл")
        
        if self.state in (1,2,3) or self.anim_t > 0:
            V2 = self.V1 + self.V_body
            # КОТОРМО: V2 (итог) -> V2 (жыйынтык)
            painter.drawText(info_x, info_y + 60, f"V2 (жыйынтык): {V2:.1f} мл")
        else:
            painter.drawText(info_x, info_y + 60, f"V2 (жыйынтык): —")

class Lab04App(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Лабораторная №4 -> №4 Лабораториялык иш
        # Метод вытеснения жидкости -> Суюктукту сүрүп чыгаруу ыкмасы (же Архимед ыкмасы)
        self.setWindowTitle("№4 Лабораториялык иш — Суюктукту сүрүп чыгаруу ыкмасы")
        self.setMinimumSize(900, 560)

        self._generate_experiment()

        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 0)

        self.menzurka = MenzurkaWidget(
            total_volume=self.V_total,
            liquid_volume=self.V1,
            divisions=self.N,
            body_volume=self.V_body
        )
        left_layout.addWidget(self.menzurka, 1)

        # КОТОРМО: Опыт: Метод вытеснения... -> Тажрыйба: Суюктукту сүрүп чыгаруу ыкмасы
        lbl_title = QLabel("<b>Тажрыйба: Суюктукту сүрүп чыгаруу ыкмасы</b>")
        right_layout.addWidget(lbl_title)

        # КОТОРМО: Инструкция
        self.lbl_instructions = QLabel(
            "Нерсени мензуркага түшүрүп, деңгээлдердин айырмасы боюнча нерсенин көлөмүн аныктаңыз.\n"
            "V1, V2 жана V = V2 - V1 маанилерин миллилитр менен киргизиңиз."
        )
        self.lbl_instructions.setWordWrap(True)
        right_layout.addWidget(self.lbl_instructions)

        # Buttons
        # КОТОРМО: Опустить -> Түшүрүү
        btn_lower = QPushButton("Түшүрүү")
        btn_lower.clicked.connect(self.menzurka.start_lower)
        # КОТОРМО: Поднять -> Көтөрүү
        btn_raise = QPushButton("Көтөрүү")
        btn_raise.clicked.connect(self.menzurka.start_raise)
        # Авто - Авто
        btn_auto = QPushButton("Авто")
        btn_auto.clicked.connect(self.menzurka.set_auto)
        
        # КОТОРМО: Случайный эксперимент -> Кокустан тандалган тажрыйба
        btn_random = QPushButton("Кокустан тандалган тажрыйба")
        btn_random.clicked.connect(self._on_random)
        # КОТОРМО: Сброс -> Кайра баштоо
        btn_reset = QPushButton("Кайра баштоо")
        btn_reset.clicked.connect(self._on_reset)

        right_layout.addWidget(btn_lower)
        right_layout.addWidget(btn_raise)
        right_layout.addWidget(btn_auto)
        right_layout.addSpacing(6)
        right_layout.addWidget(btn_random)
        right_layout.addWidget(btn_reset)

        # Input fields
        right_layout.addSpacing(8)
        # КОТОРМО: Ввод ответов -> Жоопторду киргизүү
        right_layout.addWidget(QLabel("<b>Жоопторду киргизүү</b>"))
        
        self.input_V1 = QLineEdit()
        self.input_V1.setPlaceholderText("V1 маанисин киргизиңиз, мл")
        self.input_V2 = QLineEdit()
        self.input_V2.setPlaceholderText("V2 маанисин киргизиңиз, мл")
        self.input_V = QLineEdit()
        self.input_V.setPlaceholderText("V = V2 - V1 маанисин киргизиңиз, мл")
        
        right_layout.addWidget(self.input_V1)
        right_layout.addWidget(self.input_V2)
        right_layout.addWidget(self.input_V)

        # КОТОРМО: Проверить -> Текшерүү
        btn_check = QPushButton("Текшерүү")
        btn_check.clicked.connect(self._on_check)
        # КОТОРМО: Показать ответ -> Жоопту көрсөтүү
        btn_show = QPushButton("Жоопту көрсөтүү")
        btn_show.clicked.connect(self._on_show)
        
        right_layout.addWidget(btn_check)
        right_layout.addWidget(btn_show)

        self.lbl_result = QLabel("")
        self.lbl_result.setWordWrap(True)
        right_layout.addWidget(self.lbl_result)
        right_layout.addStretch(1)

        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(120)

    def _generate_experiment(self):
        # total volume 200..800 ml for nicer visuals
        self.V_total = random.randint(200, 800)
        self.N = random.choice([10, 20, 50])
        # choose V1 so that body fits
        max_body = max(5, int(self.V_total * 0.25))
        self.V_body = random.randint(5, max_body)
        # choose V1 between 10 and V_total - V_body - 10
        self.V1 = random.randint(10, max(20, self.V_total - self.V_body - 10))
        # price per division
        self.price = self.V_total / self.N

    def _on_random(self):
        self._generate_experiment()
        # recreate menzurka widget with new params
        parent = self.menzurka.parent()
        layout = self.menzurka.parent().layout()
        # replace widget
        self.menzurka.deleteLater()
        self.menzurka = MenzurkaWidget(
            total_volume=self.V_total,
            liquid_volume=self.V1,
            divisions=self.N,
            body_volume=self.V_body
        )
        # left layout is index 0 in main layout
        left_col = self.layout().itemAt(0).layout().itemAt(0).layout()
        # remove old and add new
        while left_col.count():
            item = left_col.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        left_col.addWidget(self.menzurka, 1)

    def _on_reset(self):
        # reset animation to initial state
        self.menzurka.state = 0
        self.menzurka.anim_t = 0.0
        self.input_V1.clear()
        self.input_V2.clear()
        self.input_V.clear()
        self.lbl_result.setText("")
        self.menzurka.update()

    def _update_ui(self):
        # update shown V1 in menzurka (it uses internal values)
        # nothing else needed; menzurka repaints itself
        pass

    def _on_check(self):
        try:
            user_V1 = float(self.input_V1.text())
            user_V2 = float(self.input_V2.text())
            user_V = float(self.input_V.text())
        except Exception:
            # КОТОРМО: Ошибка -> Ката
            QMessageBox.warning(self, "Ката", "V1, V2 жана V талааларына сан маанилерин киргизиңиз.")
            return

        true_V1 = float(self.V1)
        true_V2 = float(self.V1 + self.V_body)
        true_V = float(self.V_body)

        tol_level = max(0.5, self.price)
        tol_V = max(0.5, true_V * 0.01)

        ok_V1 = abs(user_V1 - true_V1) <= tol_level
        ok_V2 = abs(user_V2 - true_V2) <= tol_level
        ok_V = abs(user_V - true_V) <= tol_V

        lines = []
        if ok_V1:
            lines.append("✅ V1 туура эсептелди.")
        else:
            lines.append(f"❌ V1 туура эмес. Туурасы: {true_V1:.1f} мл ( piela ±{tol_level:.2f} мл).")
        
        if ok_V2:
            lines.append("✅ V2 туура эсептелди.")
        else:
            lines.append(f"❌ V2 туура эмес. Туурасы: {true_V2:.1f} мл ( piela ±{tol_level:.2f} мл).")
            
        if ok_V:
            lines.append("✅ Нерсенин көлөмү V туура эсептелди.")
        else:
            lines.append(f"❌ Нерсенин көлөмү V туура эмес. Туурасы: {true_V:.1f} мл ( piela ±{tol_V:.2f} мл).")

        self.lbl_result.setText("\n".join(lines))

    def _on_show(self):
        true_V1 = float(self.V1)
        true_V2 = float(self.V1 + self.V_body)
        true_V = float(self.V_body)
        self.input_V1.setText(f"{true_V1:.2f}")
        self.input_V2.setText(f"{true_V2:.2f}")
        self.input_V.setText(f"{true_V:.2f}")
        # КОТОРМО: Показаны правильные значения -> Туура маанилер көрсөтүлдү
        self.lbl_result.setText("Туура маанилер көрсөтүлдү.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Lab04App()
    win.show()
    sys.exit(app.exec())
