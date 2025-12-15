# lab_lens_animated.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox, QComboBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
from PySide6.QtCore import Qt, QTimer, QPointF

# --- Жардамчы функциялар ---
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

# --- Аналогдук прибор ---
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

# --- Анимацияланган линза виджети ---
class LensWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(820, 420)
        # Параметрлер
        self.f = 120.0
        self.do = 260.0
        self.h_obj = 90.0
        # Анимация
        self.t = 0.0
        self.t_dir = 1.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(30)
        self.dragging = False
        self.drag_offset = 0
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
        self.t += 0.02 * self.t_dir
        if self.t >= 1.0:
            self.t = 1.0
            self.t_dir = -1.0
        elif self.t <= 0.0:
            self.t = 0.0
            self.t_dir = 1.0
        self.update()

    def mousePressEvent(self, event):
        x = event.position().x()
        y = event.position().y()
        cx = self.width() // 2
        obj_x = cx - int(self.do)
        obj_top_y = self.height()//2 - int(self.h_obj)
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

        # Оптикалык ок
        p.setPen(QPen(Qt.black, 1, Qt.DashLine))
        p.drawLine(0, baseline, w, baseline)

        # Шкала
        scale_y = 24
        p.setPen(QPen(Qt.black,1))
        p.drawLine(20, scale_y, w-20, scale_y)
        for x in range(20, w-19, 20):
            p.drawLine(x, scale_y-6, x, scale_y+6)
        p.setPen(QPen(QColor(30,120,200),2))
        p.drawLine(cx, scale_y-12, cx, scale_y+12)
        # КОТОРМО: Lens -> Линза
        p.setFont(QFont("Sans",9))
        p.drawText(cx-10, scale_y-16, "Линза")

        # Линза
        lens_w = 14
        p.setPen(QPen(QColor(30,120,200), 2))
        p.setBrush(QColor(200,230,255, 200))
        p.drawRoundedRect(cx - lens_w//2, baseline - 160, lens_w, 320, 10, 10)

        # Фокустар
        f_px = self.f
        p.setPen(QPen(QColor(200,30,30), 1, Qt.DashLine))
        p.drawLine(cx - f_px, baseline - 8, cx - f_px, baseline + 8)
        p.drawLine(cx + f_px, baseline - 8, cx + f_px, baseline + 8)
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",9))
        p.drawText(cx - f_px - 18, baseline + 22, "F")
        p.drawText(cx + f_px - 6, baseline + 22, "F'")

        # Предмет
        obj_x = cx - int(self.do)
        obj_top_y = baseline - int(self.h_obj)
        p.setPen(QPen(Qt.black,2)); p.setBrush(QColor(60,60,60))
        p.drawLine(obj_x, baseline, obj_x, obj_top_y)
        tri = QPolygonF([QPointF(obj_x, obj_top_y),
                         QPointF(obj_x - 12, obj_top_y + 18),
                         QPointF(obj_x + 12, obj_top_y + 18)])
        p.drawPolygon(tri)
        p.setFont(QFont("Sans",9))
        p.drawText(obj_x - 18, scale_y + 6, f"d={int(self.do)} px")

        # Сүрөттөлүш
        self.update_image()
        di = self.di
        img_x = None
        img_h = None
        if di is None or math.isinf(di):
            img_x = None
        else:
            img_x = cx + int(di)
            img_h = int(abs(self.m) * self.h_obj) if self.m is not None else 0

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

        # Нурлар
        p.setPen(QPen(QColor(220,100,40), 2))
        x0, y0 = obj_x, obj_top_y
        x_mid, y_mid = cx, obj_top_y
        
        # Нур 1: Параллель -> Фокус
        seg1_x = x0 + (x_mid - x0) * self.t
        seg1_y = y0
        p.drawLine(x0, y0, seg1_x, seg1_y)
        
        if img_x is not None and not math.isinf(di):
            if self.di > 0:
                x_after = x_mid + (img_x - x_mid) * self.t
                y_after = y_mid + (baseline + img_h - y_mid) * self.t
                p.drawLine(x_mid, y_mid, x_after, y_after)
            else:
                p.setPen(QPen(QColor(220,100,40), 1, Qt.DashLine))
                p.drawLine(x_mid, y_mid, cx + f_px, y_mid - ( (cx + f_px) - x_mid ) * ((baseline - y_mid)/(cx + f_px - x_mid + 1e-6)))
                p.setPen(QPen(QColor(220,100,40), 2))
        else:
            p.drawLine(x_mid, y_mid, w, y_mid)

        # Нур 2: Борбор аркылуу
        p.setPen(QPen(QColor(40,80,200), 2))
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

        # Нур 3: Фокус -> Параллель
        p.setPen(QPen(QColor(80,160,80), 2))
        fx = cx - f_px
        if self.t < 0.6:
            t3 = self.t / 0.6
            x3 = x0 + (fx - x0) * t3
            y3 = y0 + (baseline - y0) * t3
            p.drawLine(x0, y0, x3, y3)
        else:
            t3 = (self.t - 0.6) / 0.4
            x3 = fx + (w - fx) * t3
            y3 = baseline
            p.drawLine(fx, baseline, x3, y3)
            p.drawLine(x0, y0, fx, baseline)

        # Текст
        p.setPen(QPen(Qt.black,1)); p.setFont(QFont("Sans",10))
        di_text = "∞" if (self.di is not None and math.isinf(self.di)) else (f"{self.di:.1f}" if self.di is not None else "—")
        m_text = f"{self.m:.3f}" if self.m is not None else "—"
        p.drawText(12, 18, f"F = {self.f:.1f} px")
        p.drawText(12, 36, f"d_o = {self.do:.1f} px")
        p.drawText(12, 54, f"d_i = {di_text} px")
        p.drawText(12, 72, f"m = {m_text}")

class LabLensAnimatedApp(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Линзы и изображения -> Линзалар жана сүрөттөлүштөр (анимацияланган)
        self.setWindowTitle("Лабораториялык иш — Линзалар жана сүрөттөлүштөр")
        self.setMinimumSize(1200, 700)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.lens = LensWidget()
        left.addWidget(self.lens)

        meters = QHBoxLayout()
        self.meter = MeterWidget("m")
        meters.addWidget(self.meter)
        left.addLayout(meters)

        # Правая панель
        # КОТОРМО: Заголовок
        right.addWidget(QLabel("<b>Параметрлер жана башкаруу</b>"))
        
        self.input_F = QLineEdit(); self.input_F.setPlaceholderText("мисалы 120")
        self.input_d = QLineEdit(); self.input_d.setPlaceholderText("мисалы 260")
        
        right.addWidget(QLabel("Фокус аралыгы F (пиксел)"))
        right.addWidget(self.input_F)
        right.addWidget(QLabel("Предметтин аралыгы d_o (пиксел)"))
        right.addWidget(self.input_d)

        # КОТОРМО: Быстрая регулировка -> d_o тез өзгөртүү
        right.addWidget(QLabel("d_o тез өзгөртүү"))
        self.slider_d = QSlider(Qt.Horizontal)
        self.slider_d.setRange(40, 600)
        self.slider_d.setValue(int(self.lens.do))
        self.slider_d.valueChanged.connect(self.on_slider_d)
        right.addWidget(self.slider_d)

        right.addSpacing(6)
        # КОТОРМО: Режим -> Режим
        right.addWidget(QLabel("<b>Режим</b>"))
        self.chk_manual = QCheckBox("Кол менен жазуу (авто толтуруу жок)")
        right.addWidget(self.chk_manual)

        right.addSpacing(6)
        # КОТОРМО: Поля ученика -> Окуучунун жооптору
        right.addWidget(QLabel("<b>Окуучунун жооптору</b>"))
        self.input_di_meas = QLineEdit(); self.input_di_meas.setPlaceholderText("d_i (px) — өлчөнгөн")
        self.input_m_meas = QLineEdit(); self.input_m_meas.setPlaceholderText("m — чоңойтуу")
        self.combo_type = QComboBox()
        # КОТОРМО: Типтер
        self.combo_type.addItems([
            "Сүрөттөлүштүн түрүн тандаңыз",
            "чыныгы, тескери",
            "жалган, түз"
        ])
        right.addWidget(self.input_di_meas)
        right.addWidget(self.input_m_meas)
        right.addWidget(self.combo_type)

        # Кнопки
        # КОТОРМО: Применить -> Колдонуу
        btn_apply = QPushButton("Колдонуу")
        btn_apply.clicked.connect(self.apply_params)
        # КОТОРМО: Измерить -> Өлчөө
        btn_measure = QPushButton("Өлчөө")
        btn_measure.clicked.connect(self.measure)
        # КОТОРМО: Проверить -> Текшерүү
        btn_check = QPushButton("Текшерүү")
        btn_check.clicked.connect(self.check)
        # КОТОРМО: Показать ответ -> Жоопту көрсөтүү
        btn_show = QPushButton("Жоопту көрсөтүү")
        btn_show.clicked.connect(self.show_answer)
        # КОТОРМО: Случайный -> Кокустан тандалган
        btn_random = QPushButton("Кокустан тандалган")
        btn_random.clicked.connect(self.random_example)
        # КОТОРМО: Сброс -> Кайра баштоо
        btn_reset = QPushButton("Кайра баштоо")
        btn_reset.clicked.connect(self.reset_all)

        right.addWidget(btn_apply)
        right.addWidget(btn_measure)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        right.addSpacing(8)
        # КОТОРМО: Результаты -> Жыйынтыктар
        right.addWidget(QLabel("<b>Жыйынтыктар</b>"))
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
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_meter)
        self.ui_timer.start(200)

    def _update_meter(self):
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
            QMessageBox.warning(self, "Ката", "F жана d_o сан болушу керек.")
            return
        self.lens.set_params(f=F, do=d)
        self.slider_d.setValue(int(d))
        self.update_results()
        # КОТОРМО: Параметры применены -> Параметрлер колдонулду
        self.lbl_feedback.setText("Параметрлер колдонулду.")

    def measure(self):
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Кол режими: талаалар автоматтык толтурулбайт.")
            self.update_results()
            return
        di = self.lens.di
        m = self.lens.m
        if di is None or math.isinf(di):
            self.input_di_meas.setText("")
            self.input_m_meas.setText("")
            self.combo_type.setCurrentIndex(0)
            self.lbl_feedback.setText("Сүрөттөлүш чексиздикте.")
            return
        noise_di = di * (1 + random.uniform(-0.02, 0.02))
        noise_m = m * (1 + random.uniform(-0.03, 0.03)) if m is not None else None
        self.input_di_meas.setText(f"{noise_di:.2f}")
        self.input_m_meas.setText(f"{noise_m:.3f}" if noise_m is not None else "")
        # КОТОРМО: реальное -> чыныгы, виртуальное -> жалган
        typ = "чыныгы, тескери" if di > 0 else "жалган, түз"
        self.combo_type.setCurrentText(typ)
        self.lbl_feedback.setText("Көрсөткүчтөр жазылды (кичине ката менен).")
        self.update_results()

    def classify_case(self):
        f = self.lens.f
        do = self.lens.do
        if do < f:
            # КОТОРМО: виртуальное, прямое, увеличенное
            cls = "d < F: жалган, түз, чоңойтулган"
        elif abs(do - f) < 1e-6:
            cls = "d = F: сүрөттөлүш чексиздикте"
        elif f < do < 2*f:
            cls = "F < d < 2F: чыныгы, тескери, чоңойтулган"
        elif abs(do - 2*f) < 1e-6:
            cls = "d = 2F: чыныгы, тескери, тең"
        else:
            cls = "d > 2F: чыныгы, тескери, кичирейтилген"
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
        try:
            di_user = float(self.input_di_meas.text())
            m_user = float(self.input_m_meas.text())
            type_user = self.combo_type.currentText().strip()
        except Exception:
            QMessageBox.warning(self, "Ката", "Бардык маанилерди киргизиңиз.")
            return
        di_true = self.lens.di
        m_true = self.lens.m
        tol_di = max(0.03 * abs(di_true) if di_true else 1.0, 1.0)
        tol_m = max(0.05 * abs(m_true) if m_true else 0.05, 0.02)
        ok_di = (di_true is not None and not math.isinf(di_true) and abs(di_user - di_true) <= tol_di)
        ok_m = (m_true is not None and abs(m_user - m_true) <= tol_m)
        typ_true = "чыныгы, тескери" if (di_true is not None and di_true > 0) else "жалган, түз"
        ok_type = (type_user == typ_true)
        lines = []
        if ok_di:
            lines.append("✅ d_i туура.")
        else:
            lines.append(f"❌ d_i туура эмес.")
        if ok_m:
            lines.append("✅ m туура.")
        else:
            lines.append(f"❌ m туура эмес.")
        if ok_type:
            lines.append("✅ Түрү туура.")
        else:
            lines.append(f"❌ Түрү туура эмес. Туурасы: {typ_true}.")
        self.lbl_feedback.setText("\n".join(lines))

    def show_answer(self):
        di = self.lens.di
        m = self.lens.m
        if di is None or math.isinf(di):
            self.input_di_meas.setText("")
            self.input_m_meas.setText("")
            self.combo_type.setCurrentIndex(0)
            return
        self.input_di_meas.setText(f"{di:.2f}")
        self.input_m_meas.setText(f"{m:.3f}")
        typ = "чыныгы, тескери" if di > 0 else "жалган, түз"
        self.combo_type.setCurrentText(typ)
        self.lbl_feedback.setText("Туура маанилер көрсөтүлдү.")
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
        self.lbl_feedback.setText("Жаңы тажрыйба даярдалды.")

    def reset_all(self):
        self.input_F.clear(); self.input_d.clear()
        self.slider_d.setValue(int(self.lens.do))
        self.lens.set_params(f=120.0, do=260.0)
        self.update_results()
        self.input_di_meas.clear(); self.input_m_meas.clear(); self.combo_type.setCurrentIndex(0)
        self.chk_manual.setChecked(False)
        self.lbl_feedback.setText("Тазаланды.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabLensAnimatedApp()
    win.show()
    sys.exit(app.exec())