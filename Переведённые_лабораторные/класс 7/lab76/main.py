# lab_spring.py
# Требуется: pip install PySide6
import sys
import math
import random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer, QPointF

G = 9.81  # м/с^2

class SpringWidget(QFrame):
    """
    Виджет пружины с анимацией. Поддерживает состояние: груз подвешен / снят.
    При подвешенном грузе пружина стремится к равновесию, вычисленному по k_true.
    При снятом грузе пружина возвращается к естественной длине.
    """
    def __init__(self, natural_length_px=140, px_per_cm=12.0, parent=None):
        super().__init__(parent)
        self.setMinimumSize(520, 520)
        self.natural_length_px = natural_length_px
        self.px_per_cm = px_per_cm

        # экспериментальные параметры (будут задаваться извне)
        self.mass_on_hook = 50.0  # граммы
        self.k_true = 15.0  # Н/м (эталон, гарантированно != 0)

        # положение груза (текущее и целевое)
        self.hook_x = self.width() // 2
        self.hook_y0 = 80
        self.hook_y = self.hook_y0 + self.natural_length_px
        self.target_hook_y = self.hook_y

        # флаги
        self.attached = True  # груз подвешен или снят
        self.dragging = False
        self.r = 18

        # анимация (простая модель)
        self.velocity = 0.0
        self.damping = 0.12
        self.stiffness_vis = 0.9

        # таймер
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(30)

    def set_experiment(self, mass_grams=None, k_true=None, attached=True):
        if mass_grams is not None:
            self.mass_on_hook = mass_grams
        if k_true is not None and abs(k_true) > 1e-6:
            self.k_true = k_true
        self.attached = attached
        self._update_target_position()
        # мгновенно установить текущее положение в цель для аккуратного старта
        self.hook_y = self.target_hook_y
        self.velocity = 0.0
        self.update()

    def _update_target_position(self):
        """Устанавливает target_hook_y в зависимости от attached и k_true."""
        if self.attached:
            # равновесное удлинение x_eq (м): k * x = m * g
            m_kg = max(0.0, self.mass_on_hook) / 1000.0
            if abs(self.k_true) < 1e-6:
                x_eq_m = 0.0
            else:
                x_eq_m = (m_kg * G) / self.k_true
            x_eq_cm = x_eq_m * 100.0
            x_eq_px = x_eq_cm * self.px_per_cm
            self.target_hook_y = self.hook_y0 + self.natural_length_px + x_eq_px
        else:
            # груз снят — пружина в естественной длине
            self.target_hook_y = self.hook_y0 + self.natural_length_px

    def on_timer(self):
        # анимируем движение к target_hook_y, если не перетаскивают
        if not self.dragging:
            dy = self.target_hook_y - self.hook_y
            force = self.stiffness_vis * dy
            self.velocity += force * 0.18
            self.velocity *= (1.0 - self.damping)
            self.hook_y += self.velocity * 0.6
            if abs(self.hook_y - self.target_hook_y) < 0.5 and abs(self.velocity) < 0.5:
                self.hook_y = self.target_hook_y
                self.velocity = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width(); h = self.height()
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        cx = w // 2
        # точка крепления
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QColor(80, 80, 80))
        painter.drawEllipse(QPointF(cx, self.hook_y0), 6, 6)
        # пружина (зигзаг)
        top = QPointF(cx, self.hook_y0)
        bottom = QPointF(cx, self.hook_y)
        length_px = max(10.0, bottom.y() - top.y())
        coils = max(6, int(length_px / 10))
        amplitude = 12
        prev = top
        painter.setPen(QPen(QColor(80, 120, 180), 3))
        for i in range(1, coils + 1):
            t = i / coils
            x = cx + math.sin(t * math.pi * coils) * amplitude * (1 - t*0.2)
            y = top.y() + t * length_px
            painter.drawLine(prev.x(), prev.y(), x, y)
            prev = QPointF(x, y)
        # крюк и груз
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QColor(180, 80, 80))
        painter.drawEllipse(QPointF(cx, self.hook_y + self.r + 6), self.r, self.r)
        # подписи: состояние, x, F, k (скрыт)
        x_cm = self.current_extension_cm()
        F_N = self.current_force_N() if self.attached else 0.0
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Sans", 11))
        painter.drawText(12, 20, f"Абалы: {'ээгелген' if self.attached else 'алынды'}")
        painter.drawText(12, 40, f"Узартылышы x = {x_cm:.2f} см")
        painter.drawText(12, 60, f"Күч F = {F_N:.2f} Н")
        painter.drawText(12, 80, f"Жүктүн массасы = {self.mass_on_hook:.1f} г")
        # шкала слева
        scale_x = 40
        scale_top = self.hook_y0 + 10
        scale_bottom = self.hook_y0 + self.natural_length_px + int(30 * self.px_per_cm)
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(scale_x, scale_top, scale_x, scale_bottom)
        max_cm = int((scale_bottom - scale_top) / self.px_per_cm) + 2
        for i in range(max_cm + 1):
            y = scale_top + i * self.px_per_cm
            if i % 5 == 0:
                painter.drawLine(scale_x - 8, y, scale_x, y)
                painter.drawText(scale_x - 40, y + 4, f"{i} см")
            else:
                painter.drawLine(scale_x - 5, y, scale_x, y)

    def mousePressEvent(self, event):
        p = event.position()
        cx = self.width() // 2
        dist = math.hypot(p.x() - cx, p.y() - (self.hook_y + self.r + 6))
        if dist <= self.r + 6:
            self.dragging = True
            self.velocity = 0.0

    def mouseMoveEvent(self, event):
        if not self.dragging:
            return
        p = event.position()
        min_y = self.hook_y0 + 20
        max_y = self.hook_y0 + int(self.natural_length_px + 30 * self.px_per_cm)
        new_y = max(min_y, min(max_y, p.y() - self.r - 6))
        self.hook_y = new_y
        # при ручном перемещении временно синхронизируем target, чтобы не дергало
        self.target_hook_y = self.hook_y
        self.update()

    def mouseReleaseEvent(self, event):
        if not self.dragging:
            return
        self.dragging = False
        # после отпускания: если груз подвешен — пересчитать равновесие и анимировать к нему
        self._update_target_position()
        self.update()

    def current_extension_cm(self):
        current_len_px = (self.hook_y - self.hook_y0)
        ext_px = current_len_px - self.natural_length_px
        return ext_px / self.px_per_cm  # в см (может быть отрицательным)

    def current_force_N(self):
        if not self.attached:
            return 0.0
        m_kg = max(0.0, self.mass_on_hook) / 1000.0
        return m_kg * G

class LabSpringApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык — Пружина жана динамометр")
        self.setMinimumSize(1200, 700)

        self._generate_experiment()

        main_layout = QHBoxLayout(self)
        left_col = QVBoxLayout()
        right_col = QVBoxLayout()
        main_layout.addLayout(left_col, 1)
        main_layout.addLayout(right_col, 0)

        # виджет пружины
        self.spring_widget = SpringWidget(natural_length_px=140, px_per_cm=12.0)
        # гарантируем ненулевой k_true
        if abs(self.k_true) < 1e-3:
            self.k_true = 10.0
        self.spring_widget.set_experiment(mass_grams=self.mass_grams, k_true=self.k_true, attached=True)

        left_col.addWidget(self.spring_widget, 1)

        # правая панель
        right_col.addWidget(QLabel("<b>Пружина жана динамометр</b>"))
        info = QLabel(
            "Пружинага жүк ээгелесе же алсаңыз. Пружина жүк ээгелгенде созулат\n"
            "жана жүк алынганда кыскарат. Параметр k (катуулук) кездейсоқ түзүлгөн жана жашырын.\n"
            "Студент k аша эсептеп, аны киргизүүсү керек (Н/м сордо)."
        )
        info.setWordWrap(True)
        right_col.addWidget(info)

        # текущие значения
        self.lbl_current = QLabel("x = 0.00 см\nF = 0.00 Н\nАбалы: —")
        right_col.addWidget(self.lbl_current)

        # поля ввода и кнопки
        right_col.addSpacing(6)
        right_col.addWidget(QLabel("<b>Параметрлер жана текшерүү</b>"))
        self.input_mass = QLineEdit(); self.input_mass.setPlaceholderText("Жүктүн массасы, г")
        self.input_mass.setText(f"{self.mass_grams:.1f}")
        self.input_k = QLineEdit(); self.input_k.setPlaceholderText("k (Н/м) — эсептеп, киргизиңиз")
        right_col.addWidget(self.input_mass)
        right_col.addWidget(self.input_k)

        btn_update = QPushButton("Массаны жаңыртуу")
        btn_update.clicked.connect(self.update_mass)
        btn_toggle = QPushButton("Ээгелесе / Алуу жүк")
        btn_toggle.clicked.connect(self.toggle_attach)
        btn_check = QPushButton("k текшерүү")
        btn_check.clicked.connect(self.check_k)
        btn_show = QPushButton("k көрсөтүү (текшерүү үчүн)")
        btn_show.clicked.connect(self.show_k)
        btn_random = QPushButton("Кездейсоқ эксперимент")
        btn_random.clicked.connect(self.random_experiment)
        btn_reset = QPushButton("Баштапкы абалга")
        btn_reset.clicked.connect(self.reset_experiment)

        right_col.addWidget(btn_update)
        right_col.addWidget(btn_toggle)
        right_col.addWidget(btn_check)
        right_col.addWidget(btn_show)
        right_col.addWidget(btn_random)
        right_col.addWidget(btn_reset)

        right_col.addStretch(1)

        # UI-таймер
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.start(120)

    def _generate_experiment(self):
        # случайная масса и случайный k_true (Н/м), k_true != 0
        self.mass_grams = random.choice([200, 500, 1000, 1500])
        self.k_true = random.uniform(20.0, 200.0)  # Н/м, диапазон для школьного эксперимента
        if abs(self.k_true) < 1e-3:
            self.k_true = 50.0

    def update_ui(self):
        x_cm = self.spring_widget.current_extension_cm()
        F_N = self.spring_widget.current_force_N()
        state = "ээгелген" if self.spring_widget.attached else "алынды"
        self.lbl_current.setText(f"x = {x_cm:.2f} см\nF = {F_N:.2f} Н\nАбалы: {state}")

    def update_mass(self):
        try:
            m = float(self.input_mass.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "Массаны граммда санга түрүндө киргизиңиз.")
            return
        self.spring_widget.mass_on_hook = m
        self.spring_widget._update_target_position()
        self.spring_widget.update()

    def toggle_attach(self):
        # переключаем состояние подвешен/снят
        self.spring_widget.attached = not self.spring_widget.attached
        self.spring_widget._update_target_position()
        self.spring_widget.update()

    def check_k(self):
        try:
            user_k = float(self.input_k.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "k сандык маанисин киргизиңиз (Н/м).")
            return
        true_k = float(self.k_true)
        tol = max(0.05 * true_k, 0.5)  # 5% или 0.5 Н/м
        if abs(user_k - true_k) <= tol:
            QMessageBox.information(self, "Жыйынтык", "✅ k туура эсептелди.")
        else:
            QMessageBox.information(self, "Жыйынтык", f"❌ k туура эмес. Туура k ≈ {true_k:.2f} Н/м (чектөө ±{tol:.2f}).")

    def show_k(self):
        # показать k (для проверки/учителя)
        QMessageBox.information(self, "Эталон k", f"Түзүлгөн k = {self.k_true:.3f} Н/м")

    def random_experiment(self):
        self._generate_experiment()
        self.input_mass.setText(f"{self.mass_grams:.1f}")
        # по умолчанию груз подвешен
        self.spring_widget.set_experiment(mass_grams=self.mass_grams, k_true=self.k_true, attached=True)
        self.update_ui()

    def reset_experiment(self):
        # вернуть текущее состояние к начальным параметрам (не менять k)
        self.spring_widget.set_experiment(mass_grams=self.mass_grams, k_true=self.k_true, attached=True)
        self.input_k.clear()
        self.input_mass.setText(f"{self.mass_grams:.1f}")
        self.update_ui()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabSpringApp()
    win.show()
    sys.exit(app.exec())
