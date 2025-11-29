# lab_lens_animated.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox, QComboBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
from PySide6.QtCore import Qt, QTimer, QPointF

# --- Вспомогательные функции ---
def lens_image_distance(f, do):
    if abs(do) < 1e-9:
        return None
    denom = (1.0 / f) - (1.0 / do)
    if abs(denom) < 1e-12:
        return float('inf')
    return 1.0 / denom

def magnification(di, do):
    if do == 0 or di is None:
        return None
    return -di / do

# --- Универсальный аналоговый прибор (в стиле предыдущих работ) ---
class MeterWidget(QFrame):
    def __init__(self, kind="M", parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.kind = kind
        self.value = 0.0
        self.max_display = 1.0

    def set_value(self, val, vmax=None):
        self.value = val if val is not None else 0.0
        if vmax is not None:
            self.max_display = max(1e-6, float(vmax))
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
        p.setPen(QPen(Qt.black,2)); p.setFont(QFont("Sans",12,QFont.Bold))
        p.drawText(cx-8, cy+6, self.kind)
        p.setFont(QFont("Sans",9))
        p.drawText(8, h-10, f"{self.value:.3f}")

# --- Виджет линзы с анимацией лучей и перетаскиванием предмета ---
class LensWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(820, 420)
        # параметры (в пикселях для визуализации)
        self.f = 120.0
        self.do = 260.0
        self.h_obj = 90.0
        # анимация лучей: параметр t от 0..1 для движения точек по лучам
        self.t = 0.0
        self.t_dir = 1.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(30)  # ~33 FPS
        # перетаскивание предмета
        self.dragging = False
        self.drag_offset = 0
        # вычисления
        self.update_image()

    def set_params(self, f=None, do=None, h_obj=None):
        if f is not None: self.f = float(f)
        if do is not None: self.do = float(do)
        if h_obj is not None: self.h_obj = float(h_obj)
        self.update_image()
        self.update()

    def update_image(self):
        try:
            di = lens_image_distance(self.f, self.do)
        except Exception:
            di = None
        self.di = di
        self.m = magnification(di, self.do) if di is not None else None

    def _animate(self):
        # плавное движение параметра t
        self.t += 0.02 * self.t_dir
        if self.t >= 1.0:
            self.t = 1.0
            self.t_dir = -1.0
        elif self.t <= 0.0:
            self.t = 0.0
            self.t_dir = 1.0
        self.update()

    # --- мышь: перетаскивание предмета по оси ---
    def mousePressEvent(self, event):
        x = event.position().x()
        y = event.position().y()
        cx = self.width() // 2
        obj_x = cx - int(self.do)
        obj_top_y = self.height()//2 - int(self.h_obj)
        # если клик рядом со стержнем предмета — начинаем перетаскивание
        if abs(x - obj_x) < 12 and abs(y - (obj_top_y + self.h_obj/2)) < 40:
            self.dragging = True
            self.drag_offset = x - obj_x
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if not self.dragging:
            return
        x = event.position().x()
        cx = self.width() // 2
        new_obj_x = x - self.drag_offset
        # ограничим движение: предмет слева от линзы, но не слишком далеко
        min_x = 40
        max_x = cx - 40
        new_obj_x = max(min_x, min(max_x, new_obj_x))
        self.do = cx - new_obj_x
        self.update_image()
        self.update()

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))
        cx = w // 2
        baseline = h // 2

        # оптическая ось
        p.setPen(QPen(Qt.black, 1, Qt.DashLine))
        p.drawLine(0, baseline, w, baseline)

        # шкала сверху (как мензурка): деления и числа
        scale_y = 24
        p.setPen(QPen(Qt.black,1))
        p.drawLine(20, scale_y, w-20, scale_y)
        # центр линзы на шкале
        for x in range(20, w-19, 20):
            # отметки каждые 20 px
            p.drawLine(x, scale_y-6, x, scale_y+6)
        # отметка центра
        p.setPen(QPen(QColor(30,120,200),2))
        p.drawLine(cx, scale_y-12, cx, scale_y+12)
        p.setFont(QFont("Sans",9))
        p.drawText(cx-10, scale_y-16, "Lens")

        # линза (вертикальная)
        lens_w = 14
        p.setPen(QPen(QColor(30,120,200), 2))
        p.setBrush(QColor(200,230,255, 200))
        p.drawRoundedRect(cx - lens_w//2, baseline - 160, lens_w, 320, 10, 10)

        # фокусы
        f_px = self.f
        p.setPen(QPen(QColor(200,30,30), 1, Qt.DashLine))
        p.drawLine(cx - f_px, baseline - 8, cx - f_px, baseline + 8)
        p.drawLine(cx + f_px, baseline - 8, cx + f_px, baseline + 8)
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",9))
        p.drawText(cx - f_px - 18, baseline + 22, "F")
        p.drawText(cx + f_px - 6, baseline + 22, "F'")

        # предмет (стрелка) — положение зависит от self.do
        obj_x = cx - int(self.do)
        obj_top_y = baseline - int(self.h_obj)
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(60,60,60))
        p.drawLine(obj_x, baseline, obj_x, obj_top_y)
        # наконечник стрелки (треугольник)
        tri = QPolygonF([QPointF(obj_x, obj_top_y),
                         QPointF(obj_x - 12, obj_top_y + 18),
                         QPointF(obj_x + 12, obj_top_y + 18)])
        p.drawPolygon(tri)
        # подпись расстояния do (как на мензурке)
        p.setFont(QFont("Sans",9))
        p.drawText(obj_x - 18, scale_y + 6, f"d={int(self.do)} px")

        # вычисления изображения
        self.update_image()
        di = self.di
        img_x = None
        img_h = None
        if di is None or math.isinf(di):
            img_x = None
        else:
            img_x = cx + int(di)
            img_h = int(abs(self.m) * self.h_obj) if self.m is not None else 0

        # изображение: реальное (вниз) или виртуное (вверх)
        if img_x is not None:
            if self.di > 0:
                top_y = baseline + img_h
                p.setPen(QPen(Qt.darkGreen,2)); p.setBrush(QColor(30,120,30))
                p.drawLine(img_x, baseline, img_x, top_y)
                tri2 = QPolygonF([QPointF(img_x, top_y),
                                  QPointF(img_x - 12, top_y - 18),
                                  QPointF(img_x + 12, top_y - 18)])
                p.drawPolygon(tri2)
            else:
                top_y = baseline - img_h
                p.setPen(QPen(Qt.darkMagenta,2)); p.setBrush(QColor(150,30,120))
                p.drawLine(img_x, baseline, img_x, top_y)
                tri2 = QPolygonF([QPointF(img_x, top_y),
                                  QPointF(img_x - 12, top_y + 18),
                                  QPointF(img_x + 12, top_y + 18)])
                p.drawPolygon(tri2)

        # --- анимированные лучи ---
        # три основных луча: параллельный->через фокус, через центр->прямой, через фокус->параллельный
        # для анимации рисуем движущиеся точки/сегменты вдоль этих линий
        # луч 1: от вершины предмета параллельно оси к линзе, затем через фокус
        p.setPen(QPen(QColor(220,100,40), 2))
        x0, y0 = obj_x, obj_top_y
        x_mid, y_mid = cx, obj_top_y
        # сегмент до линзы
        seg1_x = x0 + (x_mid - x0) * self.t
        seg1_y = y0
        p.drawLine(x0, y0, seg1_x, seg1_y)
        # после линзы: направлен к фокусу (или параллельно для виртуального)
        if img_x is not None and not math.isinf(di):
            if self.di > 0:
                # направляем к (img_x, baseline + img_h)
                x_after = x_mid + (img_x - x_mid) * self.t
                y_after = y_mid + (baseline + img_h - y_mid) * self.t
                p.drawLine(x_mid, y_mid, x_after, y_after)
            else:
                # виртуальное: луч выходит из линзы как будто от правого фокуса (пунктир)
                p.setPen(QPen(QColor(220,100,40), 1, Qt.DashLine))
                p.drawLine(x_mid, y_mid, cx + f_px, y_mid - ( (cx + f_px) - x_mid ) * ((baseline - y_mid)/(cx + f_px - x_mid + 1e-6)))
                p.setPen(QPen(QColor(220,100,40), 2))
        else:
            p.drawLine(x_mid, y_mid, w, y_mid)

        # луч 2: через центр линзы (прямой)
        p.setPen(QPen(QColor(40,80,200), 2))
        # точка движется от предмета к изображению вдоль прямой через центр
        cx_line = cx + 1
        # координаты точки на линии
        if img_x is not None and not math.isinf(di):
            x_line = x0 + (img_x - x0) * self.t
            y_line = y0 + ( (baseline + (img_h if self.di>0 else -img_h)) - y0 ) * self.t
            p.drawLine(x0, y0, x_line, y_line)
            p.drawLine(x_line, y_line, img_x, baseline + (img_h if self.di>0 else -img_h))
        else:
            x_line = x0 + (w - x0) * self.t
            y_line = y0 + ( (baseline) - y0 ) * self.t
            p.drawLine(x0, y0, x_line, y_line)
            p.drawLine(x_line, y_line, w, baseline)

        # луч 3: через фокус слева -> после линзы параллельно
        p.setPen(QPen(QColor(80,160,80), 2))
        fx = cx - f_px
        # точка движется от предмет к фокусу, затем параллельно вправо
        if self.t < 0.6:
            t3 = self.t / 0.6
            x3 = x0 + (fx - x0) * t3
            y3 = y0 + (baseline - y0) * t3
            p.drawLine(x0, y0, x3, y3)
        else:
            # после прохождения фокуса — параллельный сегмент
            t3 = (self.t - 0.6) / 0.4
            x3 = fx + (w - fx) * t3
            y3 = baseline
            p.drawLine(fx, baseline, x3, y3)
            p.drawLine(x0, y0, fx, baseline)

        # подписи численных значений
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",10))
        di_text = "∞" if (self.di is not None and math.isinf(self.di)) else (f"{self.di:.1f}" if self.di is not None else "—")
        m_text = f"{self.m:.3f}" if self.m is not None else "—"
        p.drawText(12, 18, f"F = {self.f:.1f} px")
        p.drawText(12, 36, f"d_o = {self.do:.1f} px")
        p.drawText(12, 54, f"d_i = {di_text} px")
        p.drawText(12, 72, f"m = {m_text}")

# --- Главное приложение (интерфейс и логика проверки) ---
class LabLensAnimatedApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Линзы и изображения — анимированная лабораторная")
        self.setMinimumSize(1200, 700)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        # виджет линзы
        self.lens = LensWidget()
        left.addWidget(self.lens)

        # демонстрационный прибор (показывает модуль m в условных единицах)
        meters = QHBoxLayout()
        self.meter = MeterWidget("m")
        meters.addWidget(self.meter)
        left.addLayout(meters)

        # правая панель: параметры и поля ученика
        right.addWidget(QLabel("<b>Параметры и управление</b>"))
        right.addWidget(QLabel("Фокусное расстояние F (пиксели)"))
        self.input_F = QLineEdit(); self.input_F.setPlaceholderText("например 120")
        right.addWidget(self.input_F)
        right.addWidget(QLabel("Расстояние предмета d_o (пиксели)"))
        self.input_d = QLineEdit(); self.input_d.setPlaceholderText("например 260")
        right.addWidget(self.input_d)

        right.addWidget(QLabel("Быстрая регулировка d_o"))
        self.slider_d = QSlider(Qt.Horizontal)
        self.slider_d.setRange(40, 600)
        self.slider_d.setValue(int(self.lens.do))
        self.slider_d.valueChanged.connect(self.on_slider_d)
        right.addWidget(self.slider_d)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Режим</b>"))
        self.chk_manual = QCheckBox("Ручной режим (ученик сам записывает показания)")
        right.addWidget(self.chk_manual)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Поля ученика (введите свои измерения)</b>"))
        self.input_di_meas = QLineEdit(); self.input_di_meas.setPlaceholderText("d_i (px) — измеренное")
        self.input_m_meas = QLineEdit(); self.input_m_meas.setPlaceholderText("m — измеренное увеличение")
        self.combo_type = QComboBox()
        self.combo_type.addItems([
            "Выберите тип изображения",
            "реальное, перевёрнутое",
            "виртуальное, прямое"
        ])
        right.addWidget(self.input_di_meas)
        right.addWidget(self.input_m_meas)
        right.addWidget(self.combo_type)

        # кнопки
        btn_apply = QPushButton("Применить")
        btn_apply.clicked.connect(self.apply_params)
        btn_measure = QPushButton("Измерить (имитация)")
        btn_measure.clicked.connect(self.measure)
        btn_check = QPushButton("Проверить")
        btn_check.clicked.connect(self.check)
        btn_show = QPushButton("Показать ответ")
        btn_show.clicked.connect(self.show_answer)
        btn_random = QPushButton("Случайный пример")
        btn_random.clicked.connect(self.random_example)
        btn_reset = QPushButton("Сброс")
        btn_reset.clicked.connect(self.reset_all)

        right.addWidget(btn_apply)
        right.addWidget(btn_measure)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        right.addSpacing(8)
        right.addWidget(QLabel("<b>Результаты и подсказки</b>"))
        self.lbl_di = QLabel("d_i: —")
        self.lbl_m = QLabel("m: —")
        self.lbl_type = QLabel("Класс: —")
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setWordWrap(True)
        right.addWidget(self.lbl_di)
        right.addWidget(self.lbl_m)
        right.addWidget(self.lbl_type)
        right.addWidget(self.lbl_feedback)
        right.addStretch(1)

        self.random_example()
        # обновление прибора (демонстрационного) по таймеру
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_meter)
        self.ui_timer.start(200)

    def _update_meter(self):
        # показываем модуль m на приборе (условно)
        m = self.lens.m if self.lens.m is not None and not math.isinf(self.lens.m) else 0.0
        self.meter.set_value(abs(m), vmax=max(0.1, abs(m)*1.5))

    def on_slider_d(self, val):
        self.input_d.setText(str(val))
        try:
            do = float(val)
            self.lens.set_params(do=do)
            self.update_results()
        except:
            pass

    def apply_params(self):
        try:
            F = float(self.input_F.text()) if self.input_F.text().strip() else self.lens.f
            d = float(self.input_d.text()) if self.input_d.text().strip() else self.lens.do
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения F и d_o.")
            return
        self.lens.set_params(f=F, do=d)
        self.slider_d.setValue(int(d))
        self.update_results()
        self.lbl_feedback.setText("Параметры применены. Перетащите предмет мышью или нажмите «Измерить».")

    def measure(self):
        # автоматическое заполнение (если не ручной режим)
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Ручной режим: поля не заполняются автоматически.")
            self.update_results()
            return
        di = self.lens.di
        m = self.lens.m
        if di is None or math.isinf(di):
            self.input_di_meas.setText("")
            self.input_m_meas.setText("")
            self.combo_type.setCurrentIndex(0)
            self.lbl_feedback.setText("Изображение на бесконечности или не определено; ученик должен записать наблюдение.")
            return
        # имитация измерения с небольшой погрешностью
        noise_di = di * (1 + random.uniform(-0.02, 0.02))
        noise_m = m * (1 + random.uniform(-0.03, 0.03)) if m is not None else None
        self.input_di_meas.setText(f"{noise_di:.2f}")
        self.input_m_meas.setText(f"{noise_m:.3f}" if noise_m is not None else "")
        typ = "реальное, перевёрнутое" if di > 0 else "виртуальное, прямое"
        self.combo_type.setCurrentText(typ)
        self.lbl_feedback.setText("Поля заполнены имитацией измерений (с небольшой погрешностью).")
        self.update_results()

    def classify_case(self):
        f = self.lens.f
        do = self.lens.do
        if do < f:
            cls = "d < F: виртуальное, прямое, увеличенное"
        elif abs(do - f) < 1e-6:
            cls = "d = F: изображение на бесконечности"
        elif f < do < 2*f:
            cls = "F < d < 2F: реальное, перевёрнутое, увеличенное"
        elif abs(do - 2*f) < 1e-6:
            cls = "d = 2F: реальное, перевёрнутое, равного размера"
        else:
            cls = "d > 2F: реальное, перевёрнутое, уменьшенное"
        return cls

    def update_results(self):
        di = self.lens.di
        m = self.lens.m
        di_text = "∞" if (di is not None and math.isinf(di)) else (f"{di:.1f}" if di is not None else "—")
        m_text = f"{m:.3f}" if m is not None else "—"
        self.lbl_di.setText(f"d_i = {di_text} px")
        self.lbl_m.setText(f"m = {m_text}")
        self.lbl_type.setText(f"Класс: {self.classify_case()}")

    def check(self):
        # проверка полей ученика: d_i, m и классификация
        try:
            di_user = float(self.input_di_meas.text())
            m_user = float(self.input_m_meas.text())
            type_user = self.combo_type.currentText().strip()
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения d_i и m и выберите тип изображения.")
            return
        di_true = self.lens.di
        m_true = self.lens.m
        # допуски
        tol_di = max(0.03 * abs(di_true) if di_true else 1.0, 1.0)
        tol_m = max(0.05 * abs(m_true) if m_true else 0.05, 0.02)
        ok_di = (di_true is not None and not math.isinf(di_true) and abs(di_user - di_true) <= tol_di)
        ok_m = (m_true is not None and abs(m_user - m_true) <= tol_m)
        typ_true = "реальное, перевёрнутое" if (di_true is not None and di_true > 0) else "виртуальное, прямое"
        ok_type = (type_user == typ_true)
        lines = []
        if ok_di:
            lines.append("✅ d_i измерено верно.")
        else:
            true_di_text = "∞" if (di_true is not None and math.isinf(di_true)) else (f"{di_true:.2f}" if di_true is not None else "—")
            lines.append(f"❌ d_i неверно. Правильно: {true_di_text} px (допуск ±{tol_di:.2f}).")
        if ok_m:
            lines.append("✅ m рассчитано верно.")
        else:
            true_m_text = f"{m_true:.3f}" if m_true is not None else "—"
            lines.append(f"❌ m неверно. Правильно: {true_m_text} (допуск ±{tol_m:.3f}).")
        if ok_type:
            lines.append("✅ Тип изображения определён верно.")
        else:
            lines.append(f"❌ Тип неверен. Правильно: {typ_true}.")
        self.lbl_feedback.setText("\n".join(lines))

    def show_answer(self):
        di = self.lens.di
        m = self.lens.m
        if di is None or math.isinf(di):
            self.input_di_meas.setText("")
            self.input_m_meas.setText("")
            self.combo_type.setCurrentIndex(0)
            self.lbl_feedback.setText("Изображение на бесконечности или не определено; нет числового ответа.")
            return
        self.input_di_meas.setText(f"{di:.2f}")
        self.input_m_meas.setText(f"{m:.3f}")
        typ = "реальное, перевёрнутое" if di > 0 else "виртуальное, прямое"
        self.combo_type.setCurrentText(typ)
        self.lbl_feedback.setText("Показаны правильные значения по модели.")
        self.update_results()

    def random_example(self):
        F = random.choice([80.0, 100.0, 120.0, 140.0])
        d = random.uniform(0.5*F, 3.0*F)
        self.input_F.setText(f"{F:.1f}")
        self.input_d.setText(f"{d:.1f}")
        self.slider_d.setValue(int(d))
        self.lens.set_params(f=F, do=d)
        self.update_results()
        self.input_di_meas.clear(); self.input_m_meas.clear(); self.combo_type.setCurrentIndex(0)
        self.lbl_feedback.setText("Случайный пример сгенерирован. Перетащите предмет или нажмите «Измерить».")

    def reset_all(self):
        self.input_F.clear(); self.input_d.clear()
        self.slider_d.setValue(int(self.lens.do))
        self.lens.set_params(f=120.0, do=260.0)
        self.update_results()
        self.input_di_meas.clear(); self.input_m_meas.clear(); self.combo_type.setCurrentIndex(0)
        self.chk_manual.setChecked(False)
        self.lbl_feedback.setText("Сброшено.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabLensAnimatedApp()
    win.show()
    sys.exit(app.exec())
