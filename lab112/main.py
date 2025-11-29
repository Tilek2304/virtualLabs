# lab_refractive_index.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox, QComboBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
from PySide6.QtCore import Qt, QTimer, QPointF

def safe_sin_deg(deg):
    return math.sin(math.radians(deg))

def safe_asin(x):
    # ограничение аргумента для asin
    if x >= 1.0: return math.pi/2
    if x <= -1.0: return -math.pi/2
    return math.asin(x)

class PrismWidget(QFrame):
    """
    Визуализация: источник (луч), плоская пластина/призма (прямоугольник),
    нормаль в точке падения, падающий и преломлённый лучы.
    Параметры: n_glass (модель), угол падения a_deg (в градусах).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(760, 420)
        # модель
        self.n_air = 1.0
        self.n_glass = 1.5
        self.a_deg = 30.0  # угол падения (от нормали) в градусах
        # позиция точки падения по горизонтали (px от левого края)
        self.impact_x = 360
        # анимация: движение источника луча по вертикали
        self.t = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(30)

    def set_params(self, n_glass=None, a_deg=None, impact_x=None):
        if n_glass is not None: self.n_glass = float(n_glass)
        if a_deg is not None: self.a_deg = float(a_deg)
        if impact_x is not None: self.impact_x = int(impact_x)
        self.update()

    def _animate(self):
        # небольшая пульсация для наглядности
        self.t += 0.02
        if self.t > 2*math.pi: self.t -= 2*math.pi
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))
        cx = w//2
        baseline = h//2

        # экран слева (источник) и экран справа (экран наблюдения)
        src_x = 80
        screen_x = w - 120

        # рисуем стекло (прямоугольник) в центре
        glass_w = 220; glass_h = 220
        glass_x = cx - glass_w//2; glass_y = baseline - glass_h//2
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(200,230,255,200))
        p.drawRoundedRect(glass_x, glass_y, glass_w, glass_h, 8, 8)
        # нормаль в точке падения (вертикальная линия)
        impact_x = glass_x + int((self.impact_x - 40) % glass_w)  # ограничим внутри стекла
        impact_y = baseline
        p.setPen(QPen(QColor(120,120,120),1, Qt.DashLine))
        p.drawLine(impact_x, glass_y, impact_x, glass_y + glass_h)

        # падающий луч: от источника (src_x, y_src) к точке падения
        # вычислим точку источника так, чтобы угол падения = self.a_deg
        # нормаль вертикальна, поэтому падающий луч имеет наклон tan(a) относительно нормали
        a_rad = math.radians(self.a_deg)
        # направление луча: слева сверху/снизу в зависимости от знака a_deg
        # возьмём источник на фиксированной высоте, изменяем y так, чтобы угол соответствовал
        # пусть точка падения (impact_x, impact_y)
        # падающий луч направлен из (src_x, y_src) -> (impact_x, impact_y)
        # tan(a) = (impact_y - y_src) / (impact_x - src_x)
        # => y_src = impact_y - tan(a) * (impact_x - src_x)
        dx = impact_x - src_x
        y_src = impact_y - math.tan(a_rad) * dx
        # рисуем падающий луч
        p.setPen(QPen(QColor(220,100,40), 2))
        p.drawLine(src_x, int(y_src), impact_x, impact_y)

        # преломление: по закону Снелли: n1 sin a = n2 sin b
        sin_a = math.sin(a_rad)
        ratio = (self.n_air * sin_a) / (self.n_glass if self.n_glass!=0 else 1e-9)
        # если ratio >1 -> полное внутреннее отражение (для случая n_glass < n_air)
        total_internal = False
        if abs(ratio) > 1.0:
            total_internal = True
            b_rad = None
        else:
            b_rad = safe_asin(ratio)

        # рисуем преломлённый луч внутри стекла (если нет полного отражения)
        if not total_internal and b_rad is not None:
            # внутри стекла луч идёт от impact_x,impact_y к правой границе стекла
            # угол внутри измеряется от нормали; направим луч вправо
            # dx_inside = glass_x + glass_w - impact_x
            dx_inside = (glass_x + glass_w) - impact_x
            y_inside_end = impact_y + math.tan(b_rad) * dx_inside
            p.setPen(QPen(QColor(40,80,200), 2))
            p.drawLine(impact_x, impact_y, glass_x + glass_w, int(y_inside_end))
            # после выхода из стекла луч снова преломляется в воздух (вправо)
            # вычислим выходной угол c по Snell на границе стекло->воздух: n_glass sin b = n_air sin c
            sin_c = (self.n_glass * math.sin(b_rad)) / self.n_air
            if abs(sin_c) > 1.0:
                # редкий случай, но обработаем
                c_rad = None
            else:
                c_rad = safe_asin(sin_c)
                # луч в воздухе от правой границы к экрану
                x_exit = glass_x + glass_w
                y_exit = int(y_inside_end)
                x_screen = screen_x
                dx2 = x_screen - x_exit
                y_screen = y_exit + math.tan(c_rad) * dx2
                p.setPen(QPen(QColor(40,160,40), 2))
                p.drawLine(x_exit, y_exit, x_screen, int(y_screen))
                # отметка на экране
                p.setPen(QPen(QColor(40,160,40), 1))
                p.drawEllipse(x_screen - 4, int(y_screen) - 4, 8, 8)
                p.drawText(x_screen + 8, int(y_screen) + 4, "Image")

        else:
            # полное внутреннее отражение: рисуем отражённый луч внутри стекла
            # угол отражения = угол падения внутри (b' = a' with respect to normal inside)
            # для простоты отразим симметрично
            p.setPen(QPen(QColor(180,30,30), 2, Qt.DashLine))
            # от точки падения рисуем луч влево вверх (симметрично)
            p.drawLine(impact_x, impact_y, glass_x, int(impact_y - math.tan(a_rad) * (impact_x - glass_x)))
            p.drawText(impact_x + 6, impact_y - 6, "TIR")

        # рисуем источник (лампа) как круг слева
        p.setPen(QPen(Qt.black,1)); p.setBrush(QColor(255,220,80))
        p.drawEllipse(src_x - 12, int(y_src) - 12, 24, 24)
        p.drawText(src_x - 18, int(y_src) - 18, "Lamp")

        # подписи и цифровые значения
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",10))
        p.drawText(12, 18, f"n (модель) = {self.n_glass:.3f}")
        p.drawText(12, 36, f"a = {self.a_deg:.2f}°")
        if not total_internal and b_rad is not None:
            p.drawText(12, 54, f"b (модель) = {math.degrees(b_rad):.2f}°")
        else:
            p.drawText(12, 54, "b (модель) = — (полное внутреннее отражение)")

class LabRefractiveIndexApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Показатель преломления стекла — n = sin a / sin b")
        self.setMinimumSize(1100, 700)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        # виджет призмы/пластины
        self.prism = PrismWidget()
        left.addWidget(self.prism)

        # правая панель: параметры и поля ученика
        right.addWidget(QLabel("<b>Параметры</b>"))
        right.addWidget(QLabel("Показатель преломления стекла n (модель, опционально)"))
        self.input_n = QLineEdit(); self.input_n.setPlaceholderText("например 1.50")
        right.addWidget(self.input_n)
        right.addWidget(QLabel("Угол падения a (°)"))
        self.input_a = QLineEdit(); self.input_a.setPlaceholderText("например 30")
        right.addWidget(self.input_a)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Управление</b>"))
        self.slider_a = QSlider(Qt.Horizontal)
        self.slider_a.setRange(0, 89)
        self.slider_a.setValue(int(self.prism.a_deg))
        self.slider_a.valueChanged.connect(self.on_slider_a)
        right.addWidget(self.slider_a)
        self.lbl_a = QLabel(f"a = {self.prism.a_deg:.1f}°")
        right.addWidget(self.lbl_a)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Режим</b>"))
        self.chk_manual = QCheckBox("Ручной режим (ученик сам записывает углы)")
        right.addWidget(self.chk_manual)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Поля ученика (введите измерения)</b>"))
        self.input_a_meas = QLineEdit(); self.input_a_meas.setPlaceholderText("a (°) — измеренный угол падения")
        self.input_b_meas = QLineEdit(); self.input_b_meas.setPlaceholderText("b (°) — измеренный угол преломления")
        self.input_n_user = QLineEdit(); self.input_n_user.setPlaceholderText("n — ваш расчёт")
        right.addWidget(self.input_a_meas)
        right.addWidget(self.input_b_meas)
        right.addWidget(self.input_n_user)

        # кнопки
        btn_apply = QPushButton("Применить параметры")
        btn_apply.clicked.connect(self.apply_params)
        btn_rotate = QPushButton("Повернуть луч (анимация)")
        btn_rotate.clicked.connect(self.rotate_beam)
        btn_measure = QPushButton("Измерить (имитация)")
        btn_measure.clicked.connect(self.measure)
        btn_check = QPushButton("Проверить n")
        btn_check.clicked.connect(self.check)
        btn_show = QPushButton("Показать ответ")
        btn_show.clicked.connect(self.show_answer)
        btn_random = QPushButton("Случайный эксперимент")
        btn_random.clicked.connect(self.random_experiment)
        btn_reset = QPushButton("Сброс")
        btn_reset.clicked.connect(self.reset_all)

        right.addWidget(btn_apply)
        right.addWidget(btn_rotate)
        right.addWidget(btn_measure)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        right.addSpacing(8)
        right.addWidget(QLabel("<b>Результаты и подсказки</b>"))
        self.lbl_model = QLabel("Модель: —")
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setWordWrap(True)
        right.addWidget(self.lbl_model)
        right.addWidget(self.lbl_feedback)
        right.addStretch(1)

        # старт
        self.random_experiment()
        # таймер для обновления UI
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(150)

    def on_slider_a(self, val):
        self.input_a.setText(str(val))
        self.prism.set_params(a_deg=val)
        self.lbl_a.setText(f"a = {val:.1f}°")
        self._update_ui()

    def apply_params(self):
        try:
            n = float(self.input_n.text()) if self.input_n.text().strip() else self.prism.n_glass
            a = float(self.input_a.text()) if self.input_a.text().strip() else self.prism.a_deg
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения n и a.")
            return
        self.prism.set_params(n_glass=n, a_deg=a)
        self.slider_a.setValue(int(a))
        self.lbl_feedback.setText("Параметры применены. Нажмите «Повернуть луч» или «Измерить».")
        self._update_ui()

    def rotate_beam(self):
        # небольшая анимация: изменяем угол падения циклически
        # реализуем как временное изменение a_deg в виджете
        start = max(1.0, min(80.0, self.prism.a_deg))
        end = min(85.0, start + 20.0)
        # плавно изменим угол в несколько шагов
        steps = 40
        for i in range(steps):
            a = start + (end - start) * (i / (steps-1))
            self.prism.set_params(a_deg=a)
            QApplication.processEvents()
        self.lbl_feedback.setText("Анимация завершена.")
        self._update_ui()

    def measure(self):
        # автоматическое заполнение полей (если не ручной режим)
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Ручной режим: поля не заполняются автоматически.")
            return
        # модельные значения
        a = self.prism.a_deg
        n = self.prism.n_glass
        sin_a = safe_sin_deg(a)
        # вычислим b по Снеллию
        ratio = (self.prism.n_air * sin_a) / (n if n!=0 else 1e-9)
        if abs(ratio) > 1.0:
            # полное внутреннее отражение — поле b оставим пустым
            self.input_a_meas.setText(f"{a:.2f}")
            self.input_b_meas.setText("")
            self.input_n_user.setText("")
            self.lbl_feedback.setText("Полное внутреннее отражение: внутри стекла нет преломлённого луча.")
            return
        b_rad = safe_asin(ratio)
        b_deg = math.degrees(b_rad)
        # добавим небольшую погрешность имитации
        a_meas = a * (1 + random.uniform(-0.01, 0.01))
        b_meas = b_deg * (1 + random.uniform(-0.01, 0.01))
        n_calc = math.sin(math.radians(a_meas)) / math.sin(math.radians(b_meas)) if abs(math.sin(math.radians(b_meas)))>1e-9 else None
        self.input_a_meas.setText(f"{a_meas:.2f}")
        self.input_b_meas.setText(f"{b_meas:.2f}")
        self.input_n_user.setText(f"{n_calc:.4f}" if n_calc is not None else "")
        self.lbl_feedback.setText("Поля заполнены имитацией измерений (с небольшой погрешностью).")
        self._update_ui()

    def check(self):
        try:
            a_user = float(self.input_a_meas.text())
            b_user = float(self.input_b_meas.text())
            n_user = float(self.input_n_user.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения a, b и ваш расчёт n.")
            return
        if abs(math.sin(math.radians(b_user))) < 1e-9:
            QMessageBox.information(self, "Инфо", "sin(b) слишком мал для корректного расчёта.")
            return
        n_calc = math.sin(math.radians(a_user)) / math.sin(math.radians(b_user))
        n_true = self.prism.n_glass
        tol_calc = max(0.03 * abs(n_calc), 1e-3)
        tol_true = max(0.05 * abs(n_true), 1e-3)
        ok_user = abs(n_user - n_calc) <= tol_calc
        ok_model = abs(n_calc - n_true) <= tol_true
        lines = []
        if ok_user:
            lines.append("✅ Ваш расчёт n соответствует вычислению по измерениям.")
        else:
            lines.append(f"❌ Ваш n не совпадает с расчётом по измерениям. n_расчёт = {n_calc:.4f}.")
        if ok_model:
            lines.append("✅ Измерение близко к модельному n (по симуляции).")
        else:
            lines.append(f"❌ Измерение отличается от модельного n = {n_true:.4f} (допуск ±{tol_true:.4f}).")
        self.lbl_feedback.setText("\n".join(lines))
        self._update_ui()

    def show_answer(self):
        a = self.prism.a_deg
        n = self.prism.n_glass
        sin_a = safe_sin_deg(a)
        ratio = (self.prism.n_air * sin_a) / (n if n!=0 else 1e-9)
        if abs(ratio) > 1.0:
            self.input_a_meas.setText(f"{a:.2f}")
            self.input_b_meas.setText("")
            self.input_n_user.setText("")
            self.lbl_feedback.setText("Полное внутреннее отражение: нет числового ответа для b.")
            return
        b_rad = safe_asin(ratio)
        b_deg = math.degrees(b_rad)
        n_calc = math.sin(math.radians(a)) / math.sin(math.radians(b_deg)) if abs(math.sin(math.radians(b_deg)))>1e-9 else None
        self.input_a_meas.setText(f"{a:.2f}")
        self.input_b_meas.setText(f"{b_deg:.2f}")
        self.input_n_user.setText(f"{n_calc:.4f}" if n_calc is not None else "")
        self.lbl_feedback.setText("Показаны правильные значения по модели.")
        self._update_ui()

    def random_experiment(self):
        # случайный n 1.3..1.9, угол a 5..60 (так, чтобы не всегда TIR)
        n = random.uniform(1.30, 1.90)
        a = random.uniform(5.0, 60.0)
        self.input_n.setText(f"{n:.3f}")
        self.input_a.setText(f"{a:.1f}")
        self.slider_a.setValue(int(a))
        self.prism.set_params(n_glass=n, a_deg=a)
        self.input_a_meas.clear(); self.input_b_meas.clear(); self.input_n_user.clear()
        self.lbl_feedback.setText("Случайный эксперимент сгенерирован. Нажмите «Повернуть луч» или «Измерить».")
        self._update_ui()

    def reset_all(self):
        self.input_n.clear(); self.input_a.clear()
        self.slider_a.setValue(int(self.prism.a_deg))
        self.prism.set_params(n_glass=1.5, a_deg=30.0)
        self.input_a_meas.clear(); self.input_b_meas.clear(); self.input_n_user.clear()
        self.lbl_feedback.setText("Сброшено.")
        self._update_ui()

    def _update_ui(self):
        self.lbl_model.setText(f"Модель: n={self.prism.n_glass:.3f}, a={self.prism.a_deg:.2f}°")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabRefractiveIndexApp()
    win.show()
    sys.exit(app.exec())
