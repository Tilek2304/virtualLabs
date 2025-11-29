# lab_focal_length.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
from PySide6.QtCore import Qt, QTimer, QPointF

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

class MeterWidget(QFrame):
    def __init__(self, kind="f", parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.kind = kind
        self.value = 0.0
        self.max_display = 1.0

    def set_value(self, val, vmax=None):
        self.value = val if val is not None else 0.0
        if vmax is not None:
            self.max_display = max(1e-9, float(vmax))
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

class FocalLensWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(820, 420)
        # модельные параметры (в пикселях для визуализации)
        self.f = 120.0          # фокусное расстояние в пикселях (модель)
        self.do = 260.0         # расстояние предмета (px)
        self.screen_x = self.width() - 140
        self.h_obj = 90.0
        self.t = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(30)
        self.dragging_obj = False
        self.dragging_screen = False
        self.drag_offset = 0

    def set_params(self, f=None, do=None, h_obj=None):
        if f is not None: self.f = float(f)
        if do is not None: self.do = float(do)
        if h_obj is not None: self.h_obj = float(h_obj)
        self.update()

    def _animate(self):
        self.t += 0.02
        if self.t > 2*math.pi: self.t -= 2*math.pi
        self.update()

    def mousePressEvent(self, event):
        x = event.position().x()
        y = event.position().y()
        cx = self.width()//2
        obj_x = cx - int(self.do)
        obj_y = self.height()//2 - int(self.h_obj/2)
        # если клик рядом с предметом — перетаскиваем предмет
        if abs(x - obj_x) < 12 and abs(y - (obj_y + self.h_obj/2)) < 40:
            self.dragging_obj = True
            self.drag_offset = x - obj_x
            self.setCursor(Qt.ClosedHandCursor)
            return
        # если клик рядом с экраном — перетаскиваем экран
        screen_x = self.screen_x
        if abs(x - screen_x) < 12:
            self.dragging_screen = True
            self.drag_offset = x - screen_x
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        x = event.position().x()
        cx = self.width()//2
        if self.dragging_obj:
            new_obj_x = x - self.drag_offset
            min_x = 40
            max_x = cx - 40
            new_obj_x = max(min_x, min(max_x, new_obj_x))
            self.do = cx - new_obj_x
            self.update()
        if self.dragging_screen:
            new_screen_x = x - self.drag_offset
            min_x = cx + 40
            max_x = self.width() - 40
            self.screen_x = int(max(min_x, min(max_x, new_screen_x)))
            self.update()

    def mouseReleaseEvent(self, event):
        if self.dragging_obj or self.dragging_screen:
            self.dragging_obj = False
            self.dragging_screen = False
            self.setCursor(Qt.ArrowCursor)

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(250,250,250))
        cx = w//2
        baseline = h//2

        # оптическая ось
        p.setPen(QPen(Qt.black,1, Qt.DashLine))
        p.drawLine(0, baseline, w, baseline)

        # линза
        lens_w = 14
        p.setPen(QPen(QColor(30,120,200), 2)); p.setBrush(QColor(200,230,255,200))
        p.drawRoundedRect(cx - lens_w//2, baseline - 160, lens_w, 320, 10, 10)
        # фокусы
        f_px = self.f
        p.setPen(QPen(QColor(200,30,30), 1, Qt.DashLine))
        p.drawLine(cx - f_px, baseline - 8, cx - f_px, baseline + 8)
        p.drawLine(cx + f_px, baseline - 8, cx + f_px, baseline + 8)
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",9))
        p.drawText(cx - f_px - 18, baseline + 22, "F")
        p.drawText(cx + f_px - 6, baseline + 22, "F'")

        # предмет (стрелка)
        obj_x = cx - int(self.do)
        obj_top_y = baseline - int(self.h_obj)
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(60,60,60))
        p.drawLine(obj_x, baseline, obj_x, obj_top_y)
        tri = QPolygonF([QPointF(obj_x, obj_top_y),
                         QPointF(obj_x - 12, obj_top_y + 18),
                         QPointF(obj_x + 12, obj_top_y + 18)])
        p.drawPolygon(tri)
        p.setFont(QFont("Sans",9)); p.drawText(obj_x - 18, baseline - int(self.h_obj) - 6, f"object")

        # экран
        screen_x = self.screen_x if self.screen_x is not None else w - 140
        p.setPen(QPen(QColor(80,80,80),2)); p.setBrush(QColor(240,240,240))
        p.drawRect(screen_x - 6, baseline - 160, 6, 320)
        p.setFont(QFont("Sans",9)); p.setPen(QPen(Qt.black,1))
        p.drawText(screen_x + 8, baseline - 160 + 12, "screen")

        # вычисления изображения по тонкой линзе (в пикселях -> метры условно)
        # используем модельные единицы: 1 px -> 1 условная единица длины
        do = self.do
        # переводим пиксели в "метры" для расчёта f в метрах: здесь работаем в пикселях, формула сохраняется
        # di по формуле тонкой линзы: 1/f = 1/do + 1/di  => di = 1 / (1/f - 1/do)
        # если do == f -> di = inf
        di = None
        try:
            denom = (1.0 / self.f) - (1.0 / do)
            if abs(denom) < 1e-9:
                di = float('inf')
            else:
                di = 1.0 / denom
        except Exception:
            di = None

        # позиция изображения на экране (если ди конечна)
        img_x = None
        img_h = None
        if di is not None and not math.isinf(di):
            img_x = cx + int(di)
            m = magnification(di, do)
            img_h = int(abs(m) * self.h_obj) if m is not None else 0
            # рисуем изображение на экране (перевёрнутое вниз если di>0)
            if img_x is not None:
                if di > 0:
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

        # анимированные лучи для наглядности (параллельный, через центр, через фокус)
        p.setPen(QPen(QColor(220,100,40), 2))
        x0, y0 = obj_x, obj_top_y
        # луч параллельный
        p.drawLine(x0, y0, cx - 6, y0)
        if img_x is not None and not math.isinf(di):
            p.drawLine(cx + 6, y0, img_x, baseline + (img_h if di>0 else -img_h))
        else:
            p.drawLine(cx + 6, y0, screen_x, y0)

        # луч через центр
        p.setPen(QPen(QColor(40,80,200), 2))
        if img_x is not None and not math.isinf(di):
            p.drawLine(x0, y0, img_x, baseline + (img_h if di>0 else -img_h))
        else:
            p.drawLine(x0, y0, screen_x, baseline)

        # подписи
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",10))
        di_text = "∞" if (di is not None and math.isinf(di)) else (f"{di:.1f}" if di is not None else "—")
        p.drawText(12, 18, f"f (модель) = {self.f:.1f} px")
        p.drawText(12, 36, f"d_o = {self.do:.1f} px")
        p.drawText(12, 54, f"d_i (модель) = {di_text} px")

class LabFocalApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Фокусное расстояние линзы — определение f")
        self.setMinimumSize(1200, 720)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.lens = FocalLensWidget()
        left.addWidget(self.lens)

        meters = QHBoxLayout()
        self.meter = MeterWidget("f")
        meters.addWidget(self.meter)
        left.addLayout(meters)

        right.addWidget(QLabel("<b>Параметры</b>"))
        right.addWidget(QLabel("Фокусное расстояние f (px) — модель (опционально)"))
        self.input_f = QLineEdit(); self.input_f.setPlaceholderText("например 120")
        right.addWidget(self.input_f)
        right.addWidget(QLabel("Расстояние предмета d_o (px)"))
        self.input_do = QLineEdit(); self.input_do.setPlaceholderText("например 260")
        right.addWidget(self.input_do)
        right.addWidget(QLabel("Положение экрана x (px)"))
        self.input_screen = QLineEdit(); self.input_screen.setPlaceholderText("например 980")
        right.addWidget(self.input_screen)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Режим</b>"))
        self.chk_manual = QCheckBox("Ручной режим (ученик сам записывает d_i)")
        right.addWidget(self.chk_manual)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Поля ученика (введите измерения)</b>"))
        self.input_di_meas = QLineEdit(); self.input_di_meas.setPlaceholderText("d_i (px) — измеренное расстояние изображения от линзы")
        self.input_f_user = QLineEdit(); self.input_f_user.setPlaceholderText("f (px) — ваш расчёт по тонкой линзе")
        right.addWidget(self.input_di_meas)
        right.addWidget(self.input_f_user)

        btn_apply = QPushButton("Применить параметры")
        btn_apply.clicked.connect(self.apply_params)
        btn_measure = QPushButton("Измерить (имитация)")
        btn_measure.clicked.connect(self.measure)
        btn_check = QPushButton("Проверить f")
        btn_check.clicked.connect(self.check)
        btn_show = QPushButton("Показать ответ")
        btn_show.clicked.connect(self.show_answer)
        btn_random = QPushButton("Случайный эксперимент")
        btn_random.clicked.connect(self.random_experiment)
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
        self.lbl_model = QLabel("Модель: —")
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setWordWrap(True)
        right.addWidget(self.lbl_model)
        right.addWidget(self.lbl_feedback)
        right.addStretch(1)

        self.random_experiment()
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_meter)
        self.ui_timer.start(200)

    def apply_params(self):
        try:
            f = float(self.input_f.text()) if self.input_f.text().strip() else self.lens.f
            do = float(self.input_do.text()) if self.input_do.text().strip() else self.lens.do
            screen = int(self.input_screen.text()) if self.input_screen.text().strip() else (self.lens.width() - 140)
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения f, d_o и положение экрана.")
            return
        self.lens.set_params(f=f, do=do)
        self.lens.screen_x = screen
        self.lbl_feedback.setText("Параметры применены. Перетащите предмет или экран мышью для практики.")
        self._update_meter()

    def measure(self):
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Ручной режим: поле d_i не заполняется автоматически.")
            return
        # используем модельные di и добавим шум
        do = self.lens.do
        f = self.lens.f
        try:
            denom = (1.0 / f) - (1.0 / do)
            if abs(denom) < 1e-9:
                di = float('inf')
            else:
                di = 1.0 / denom
        except Exception:
            di = None
        if di is None or math.isinf(di):
            self.input_di_meas.setText("")
            self.input_f_user.setText("")
            self.lbl_feedback.setText("Изображение на бесконечности или не определено; ученик должен записать наблюдение.")
            return
        di_meas = di * (1 + random.uniform(-0.02, 0.02))
        self.input_di_meas.setText(f"{di_meas:.2f}")
        # рассчитаем f по измерению: 1/f = 1/do + 1/di
        f_calc = 1.0 / (1.0 / do + 1.0 / di_meas) if abs(di_meas)>1e-9 else None
        if f_calc:
            self.input_f_user.setText(f"{f_calc:.2f}")
        self.lbl_feedback.setText("Поля заполнены имитацией измерений (с небольшой погрешностью).")
        self._update_meter()

    def check(self):
        try:
            di_user = float(self.input_di_meas.text())
            f_user = float(self.input_f_user.text())
            do = float(self.input_do.text()) if self.input_do.text().strip() else self.lens.do
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения d_i, f и d_o.")
            return
        if abs(di_user) < 1e-9:
            QMessageBox.information(self, "Инфо", "d_i слишком мал для корректного расчёта.")
            return
        f_calc = 1.0 / (1.0 / do + 1.0 / di_user)
        f_true = self.lens.f
        tol_calc = max(0.03 * abs(f_calc), 1e-2)
        tol_true = max(0.05 * abs(f_true), 1e-2)
        ok_user = abs(f_user - f_calc) <= tol_calc
        ok_model = abs(f_calc - f_true) <= tol_true
        lines = []
        if ok_user:
            lines.append("✅ Ваш расчёт f соответствует вычислению по измерениям.")
        else:
            lines.append(f"❌ Ваш f не совпадает с расчётом по измерениям. f_расчёт = {f_calc:.2f} px.")
        if ok_model:
            lines.append("✅ Измерение близко к модельному f (по симуляции).")
        else:
            lines.append(f"❌ Измерение отличается от модельного f = {f_true:.2f} px (допуск ±{tol_true:.2f}).")
        self.lbl_feedback.setText("\n".join(lines))
        self._update_meter()

    def show_answer(self):
        do = self.lens.do
        f = self.lens.f
        try:
            denom = (1.0 / f) - (1.0 / do)
            if abs(denom) < 1e-9:
                di = float('inf')
            else:
                di = 1.0 / denom
        except Exception:
            di = None
        if di is None or math.isinf(di):
            QMessageBox.information(self, "Инфо", "Изображение на бесконечности или не определено.")
            return
        self.input_di_meas.setText(f"{di:.2f}")
        self.input_f_user.setText(f"{f:.2f}")
        self.lbl_feedback.setText("Показаны правильные значения по модели.")
        self._update_meter()

    def random_experiment(self):
        f = random.choice([80.0, 100.0, 120.0, 140.0])
        do = random.uniform(0.6*f, 3.0*f)
        screen = self.lens.width() - 140
        self.input_f.setText(f"{f:.1f}")
        self.input_do.setText(f"{do:.1f}")
        self.input_screen.setText(str(screen))
        self.lens.set_params(f=f, do=do)
        self.lens.screen_x = screen
        self.input_di_meas.clear(); self.input_f_user.clear()
        self.lbl_feedback.setText("Случайный эксперимент сгенерирован. Перетащите предмет или экран и нажмите «Измерить».")
        self._update_meter()

    def reset_all(self):
        self.input_f.clear(); self.input_do.clear(); self.input_screen.clear()
        self.input_di_meas.clear(); self.input_f_user.clear()
        self.lens.set_params(f=120.0, do=260.0)
        self.lens.screen_x = self.lens.width() - 140
        self.lbl_feedback.setText("Сброшено.")
        self._update_meter()

    def _update_meter(self):
        self.meter.set_value(self.lens.f, vmax=max(1.0, abs(self.lens.f)*1.5))
        self.lbl_model.setText(f"Модель: f={self.lens.f:.1f} px, d_o={self.lens.do:.1f} px")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabFocalApp()
    win.show()
    sys.exit(app.exec())
