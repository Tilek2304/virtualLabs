# lab_diffraction_lambda.py
# Требуется: pip install PySide6
import sys, math, random, time
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer

# --- Вспомогательные функции ---
def calc_lambda(a_m, d_m, b_m):
    # λ = a * d / b
    if b_m == 0:
        return None
    return a_m * d_m / b_m

# --- Универсальный аналоговый прибор (демонстрационный) ---
class MeterWidget(QFrame):
    def __init__(self, kind="λ (nm)", parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 100)
        self.kind = kind
        self.value = 0.0
        self.max_display = 1.0

    def set_value(self, val, vmax=None):
        self.value = val if val is not None else 0.0
        if vmax is not None:
            self.max_display = max(1e-12, float(vmax))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w//2, h//2
        R = min(w, h)//2 - 8
        p.fillRect(self.rect(), QColor(250,250,250))
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(255,255,255))
        p.drawEllipse(cx - R, cy - R, 2*R, 2*R)
        p.setPen(QPen(Qt.black,1))
        for ang in range(-60, 61, 10):
            r = math.radians(ang)
            p.drawLine(cx + int((R-8)*math.cos(r)), cy - int((R-8)*math.sin(r)),
                       cx + int(R*math.cos(r)),       cy - int(R*math.sin(r)))
        frac = 0.0
        if self.max_display > 0:
            frac = max(0.0, min(1.0, abs(self.value) / self.max_display))
        ang = -60 + frac*120.0
        r = math.radians(ang)
        p.setPen(QPen(QColor(200,30,30),2))
        p.drawLine(cx, cy, cx + int((R-14)*math.cos(r)), cy - int((R-14)*math.sin(r)))
        p.setPen(QPen(Qt.black,2)); p.setFont(QFont("Sans",11,QFont.Bold))
        p.drawText(cx-18, cy+6, self.kind)
        p.setFont(QFont("Sans",9))
        # цифровое значение
        if abs(self.value) < 1e-12:
            p.drawText(8, h-10, "—")
        else:
            # если прибор показывает в нанометрах
            if self.kind.startswith("λ"):
                p.drawText(8, h-10, f"{self.value*1e9:.1f} nm")
            else:
                p.drawText(8, h-10, f"{self.value:.4g}")

# --- Виджет: решётка + экран + анимация интерференции ---
class DiffractionWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(820, 420)
        # модельные параметры (SI)
        self.a = 1e-6        # шаг решётки (м)
        self.d = 1.0         # расстояние до экрана (м)
        self.lambda_true = 600e-9  # истинная длина волны (м)
        # визуальные параметры
        self.screen_x = None
        self.pattern_phase = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(40)
        # для симуляции максимумов
        self.k_max = 5

    def set_params(self, a=None, d=None, lambda_true=None):
        if a is not None: self.a = float(a)
        if d is not None: self.d = float(d)
        if lambda_true is not None: self.lambda_true = float(lambda_true)
        self.update()

    def _animate(self):
        self.pattern_phase += 0.06
        if self.pattern_phase > 2*math.pi:
            self.pattern_phase -= 2*math.pi
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(20,20,30))  # тёмный фон для контраста
        cx = 120  # позиция решётки слева
        self.screen_x = w - 120
        screen_w = 20
        # рисуем решётку (символически)
        p.setPen(QPen(QColor(200,200,200), 1))
        for i in range(8):
            p.drawLine(cx + i*2, 40, cx + i*2, h-40)
        p.setFont(QFont("Sans",9)); p.setPen(QPen(Qt.white,1))
        p.drawText(cx-20, 24, "Grating")

        # рисуем экран справа
        p.setPen(QPen(QColor(180,180,200), 1)); p.setBrush(QColor(240,240,250, 40))
        p.drawRect(self.screen_x, 20, screen_w, h-40)

        # вычислим положение максимумов на экране по модели для центрального порядка m
        # для малых углов: y_m ≈ m * λ * d / a  (если a — шаг решётки, b — расстояние между максимумами b = y_{m+1}-y_m)
        # здесь используем λ = self.lambda_true
        lam = self.lambda_true
        a = self.a
        d = self.d
        # масштаб: реальное расстояние d (м) отображаем как пиксели по горизонтали между решёткой и экраном
        # пусть dx_m = screen_x - cx
        dx_m = float(self.screen_x - cx)
        # пикселей на метр по горизонтали:
        px_per_m = dx_m / max(1e-6, d)
        # вычислим координаты максимумов y на экране (в пикселях)
        center_y = h // 2
        max_positions = []
        for m in range(-self.k_max, self.k_max+1):
            y_m_real = m * lam * d / a  # метры
            y_m_px = center_y + int(y_m_real * px_per_m)
            max_positions.append((m, y_m_px))

        # рисуем интерференционную картину как яркие полосы на экране
        for (m, y_px) in max_positions:
            # яркость зависит от порядок m (главный максимум m=0 самый яркий)
            brightness = max(0.05, 1.0 - 0.12 * abs(m))
            color_val = int(255 * brightness)
            col = QColor(255, 220, 80, int(200 * brightness))
            p.setPen(Qt.NoPen); p.setBrush(col)
            # рисуем эллиптическую полосу вдоль экрана
            p.drawRect(self.screen_x, y_px - 8, screen_w, 16)

        # для наглядности нарисуем линии, соединяющие решётку и максимум (показательные лучи)
        p.setPen(QPen(QColor(200,120,40,200), 1))
        for (m, y_px) in max_positions:
            # точка на решётке (cx, center_y)
            # точка на экране (screen_x, y_px)
            # рисуем пунктирную линию
            p.setPen(QPen(QColor(200,120,40,120), 1, Qt.DashLine))
            p.drawLine(cx + 8, center_y, self.screen_x, y_px)

        # подписи и цифровые значения
        p.setPen(QPen(Qt.white,1)); p.setFont(QFont("Sans",10))
        p.drawText(12, 18, f"a (шаг решётки) = {self.a*1e6:.3f} μm")
        p.drawText(12, 36, f"d (расстояние до экрана) = {self.d:.3f} m")
        p.drawText(12, 54, f"λ (модель) = {self.lambda_true*1e9:.1f} nm")
        # подпись расстояния между соседними максимумами (b) для m=0 и m=1
        # b_real = λ * d / a
        b_real = lam * d / a if a != 0 else 0.0
        p.drawText(12, 72, f"b (модель между соседними максимумами) = {b_real*1e3:.3f} mm")

# --- Главное приложение и логика проверки ---
class LabDiffractionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Дифракция и длина волны — λ = a·d / b")
        self.setMinimumSize(1200, 720)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        # виджет дифракции
        self.diff = DiffractionWidget()
        left.addWidget(self.diff)

        # демонстрационный прибор (показывает λ в нанометрах)
        meters = QHBoxLayout()
        self.meter = MeterWidget("λ (nm)")
        meters.addWidget(self.meter)
        left.addLayout(meters)

        # правая панель: параметры и поля ученика
        right.addWidget(QLabel("<b>Параметры эксперимента</b>"))
        right.addWidget(QLabel("Шаг решётки a (μm)"))
        self.input_a = QLineEdit(); self.input_a.setPlaceholderText("например 1.00 (μm)")
        right.addWidget(self.input_a)
        right.addWidget(QLabel("Расстояние до экрана d (m)"))
        self.input_d = QLineEdit(); self.input_d.setPlaceholderText("например 1.00 (m)")
        right.addWidget(self.input_d)
        right.addWidget(QLabel("Модельная длина волны λ (nm) — опционально"))
        self.input_lambda = QLineEdit(); self.input_lambda.setPlaceholderText("например 600 (nm)")
        right.addWidget(self.input_lambda)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Режим</b>"))
        self.chk_manual = QCheckBox("Ручной режим (ученик сам записывает b)")
        right.addWidget(self.chk_manual)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Поля ученика (введите измерения)</b>"))
        self.input_b_mm = QLineEdit(); self.input_b_mm.setPlaceholderText("b (mm) — расстояние между соседними максимумами")
        self.input_lambda_user = QLineEdit(); self.input_lambda_user.setPlaceholderText("λ (nm) — ваш расчёт")
        right.addWidget(self.input_b_mm)
        right.addWidget(self.input_lambda_user)

        # кнопки
        btn_apply = QPushButton("Применить параметры")
        btn_apply.clicked.connect(self.apply_params)
        btn_simulate = QPushButton("Симулировать картину")
        btn_simulate.clicked.connect(self.simulate_pattern)
        btn_measure = QPushButton("Измерить (имитация)")
        btn_measure.clicked.connect(self.measure)
        btn_check = QPushButton("Проверить λ")
        btn_check.clicked.connect(self.check)
        btn_show = QPushButton("Показать ответ")
        btn_show.clicked.connect(self.show_answer)
        btn_random = QPushButton("Случайный эксперимент")
        btn_random.clicked.connect(self.random_experiment)
        btn_reset = QPushButton("Сброс")
        btn_reset.clicked.connect(self.reset_all)

        right.addWidget(btn_apply)
        right.addWidget(btn_simulate)
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

        # стартовые параметры
        self.random_experiment()
        # таймер для обновления прибора
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_meter)
        self.ui_timer.start(200)

    def apply_params(self):
        try:
            a_um = float(self.input_a.text()) if self.input_a.text().strip() else self.diff.a*1e6
            d_m = float(self.input_d.text()) if self.input_d.text().strip() else self.diff.d
            lam_nm = float(self.input_lambda.text()) if self.input_lambda.text().strip() else self.diff.lambda_true*1e9
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения a (μm), d (m) и (опционально) λ (nm).")
            return
        a_m = a_um * 1e-6
        lam_m = lam_nm * 1e-9
        self.diff.set_params(a=a_m, d=d_m, lambda_true=lam_m)
        self.lbl_feedback.setText("Параметры применены. Нажмите «Симулировать картину» или «Измерить».")
        self._update_meter()

    def simulate_pattern(self):
        # просто обновим виджет (анимация идёт автоматически)
        self.diff.update()
        self.lbl_feedback.setText("Симуляция интерференционной картины обновлена.")
        self._update_meter()

    def measure(self):
        # автоматическое заполнение поля b (если не ручной режим)
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Ручной режим: поле b не заполняется автоматически.")
            return
        # модельное b = λ * d / a
        a = self.diff.a
        d = self.diff.d
        lam = self.diff.lambda_true
        if a == 0:
            QMessageBox.information(self, "Инфо", "a не задано или равно нулю.")
            return
        b_real = lam * d / a  # метры
        # добавим шум и переведём в мм
        b_meas = b_real * (1 + random.uniform(-0.02, 0.02))
        b_mm = b_meas * 1e3
        self.input_b_mm.setText(f"{b_mm:.3f}")
        # рассчитаем λ по измерению и заполним поле λ (nm)
        lam_calc = calc_lambda(a, d, b_real)  # это вернёт lam (м)
        if lam_calc is not None:
            self.input_lambda_user.setText(f"{lam_calc*1e9:.1f}")
        self.lbl_feedback.setText("Поля заполнены имитацией измерений (с небольшой погрешностью).")
        self._update_meter()

    def check(self):
        try:
            b_mm = float(self.input_b_mm.text())
            lam_user_nm = float(self.input_lambda_user.text())
            a_um = float(self.input_a.text()) if self.input_a.text().strip() else self.diff.a*1e6
            d_m = float(self.input_d.text()) if self.input_d.text().strip() else self.diff.d
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения b (mm), λ (nm), a (μm) и d (m).")
            return
        # перевод единиц
        b_m = b_mm * 1e-3
        a_m = a_um * 1e-6
        lam_user = lam_user_nm * 1e-9
        if abs(b_m) < 1e-12 or abs(a_m) < 1e-12:
            QMessageBox.information(self, "Инфо", "a или b слишком малы для корректного расчёта.")
            return
        lam_calc = calc_lambda(a_m, d_m, b_m)
        lam_true = self.diff.lambda_true
        tol_calc = max(0.03 * abs(lam_calc) if lam_calc else 1e-9, 1e-9)
        tol_true = max(0.05 * abs(lam_true) if lam_true else 1e-9, 1e-9)
        ok_user = abs(lam_user - lam_calc) <= tol_calc
        ok_model = abs(lam_calc - lam_true) <= tol_true
        lines = []
        if ok_user:
            lines.append("✅ Ваш расчёт λ соответствует вычислению по измерениям.")
        else:
            lines.append(f"❌ Ваш λ не совпадает с расчётом по измерениям. λ_расчёт = {lam_calc*1e9:.1f} nm.")
        if ok_model:
            lines.append("✅ Измерение близко к модельной длине волны (по симуляции).")
        else:
            lines.append(f"❌ Измерение отличается от модельной λ = {lam_true*1e9:.1f} nm (допуск ±{tol_true*1e9:.1f} nm).")
        self.lbl_feedback.setText("\n".join(lines))
        self._update_meter()

    def show_answer(self):
        # показываем модельные значения b и λ
        a = self.diff.a
        d = self.diff.d
        lam = self.diff.lambda_true
        if a == 0:
            QMessageBox.information(self, "Инфо", "a не задано.")
            return
        b_real = lam * d / a
        self.input_b_mm.setText(f"{b_real*1e3:.3f}")
        self.input_lambda_user.setText(f"{lam*1e9:.1f}")
        self.lbl_feedback.setText("Показаны правильные значения по модели.")
        self._update_meter()

    def random_experiment(self):
        # генерируем удобные параметры: a 0.5..2.0 μm, d 0.5..2.0 m, λ 400..700 nm
        a_um = random.uniform(0.5, 2.0)
        d_m = random.uniform(0.5, 2.0)
        lam_nm = random.uniform(400.0, 700.0)
        self.input_a.setText(f"{a_um:.3f}")
        self.input_d.setText(f"{d_m:.3f}")
        self.input_lambda.setText(f"{lam_nm:.1f}")
        self.diff.set_params(a=a_um*1e-6, d=d_m, lambda_true=lam_nm*1e-9)
        self.input_b_mm.clear(); self.input_lambda_user.clear()
        self.lbl_feedback.setText("Случайный эксперимент сгенерирован. Нажмите «Симулировать картину» или «Измерить».")
        self._update_meter()

    def reset_all(self):
        self.input_a.clear(); self.input_d.clear(); self.input_lambda.clear()
        self.input_b_mm.clear(); self.input_lambda_user.clear()
        self.diff.set_params(a=1e-6, d=1.0, lambda_true=600e-9)
        self.lbl_feedback.setText("Сброшено.")
        self._update_meter()

    def _update_meter(self):
        # обновляем демонстрационный прибор (λ в nm)
        lam = self.diff.lambda_true
        self.meter.set_value(lam, vmax=max(1e-9, lam*2))
        self.lbl_model.setText(f"Модель: a={self.diff.a*1e6:.3f} μm, d={self.diff.d:.3f} m, λ={self.diff.lambda_true*1e9:.1f} nm")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabDiffractionApp()
    win.show()
    sys.exit(app.exec())
