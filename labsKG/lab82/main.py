# lab_cmp_heat.py
# Требуется: pip install PySide6
import sys, random, math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PySide6.QtCore import Qt, QTimer, QPointF

# Мектеп бирдиктери:
# масса — грамм (г), температура — °C, жылуулук сыйымдуулук — Дж/(г·°C)
C_WATER = 4.2  # c1 суу, Дж/(г·°C)

class CalorimeterWidget(QFrame):
    """
    Калориметр: суу жана ысык цилиндр.
    Цилиндрди сууга түшүрүү анимациясы. Термометр жыйынтык Т көрсөтөт.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(460, 420)
        # Параметрлер
        self.m1 = 100.0   # г (суу)
        self.t1 = 20.0    # °C
        self.c1 = C_WATER
        self.m2 = 100.0   # г (цилиндр)
        self.t2 = 90.0    # °C
        self.t_final = None
        # Анимация
        self.lowering = False
        self.anim_t = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(30)
        self.wave_phase = 0.0

    def set_params(self, m1, t1, m2, t2, c1=C_WATER):
        self.m1 = float(m1); self.t1 = float(t1)
        self.m2 = float(m2); self.t2 = float(t2)
        self.c1 = float(c1)
        self.t_final = None
        self.lowering = False
        self.anim_t = 0.0
        self.update()

    def start_lowering(self):
        self.lowering = True

    def mix(self):
        """
        Жылуулук балансы боюнча акыркы температураны эсептөө.
        c1*m1*(t - t1) = c2*m2*(t2 - t)
        """
        # Жашыруун c2 (чыныгы) маанисин колдонобуз
        c2_true = getattr(self, "c2_true", None)
        if c2_true is None:
            c2_true = random.uniform(0.2, 1.0)  # Дж/(г·°C)
            self.c2_true = c2_true

        denom = (self.c1 * self.m1 + c2_true * self.m2)
        if denom <= 1e-9:
            self.t_final = None
        else:
            self.t_final = (self.c1 * self.m1 * self.t1 + c2_true * self.m2 * self.t2) / denom
        
        self.lowering = False
        self.anim_t = 1.0
        self.update()

    def on_timer(self):
        self.wave_phase += 0.10
        if self.wave_phase > 2 * math.pi:
            self.wave_phase -= 2 * math.pi
        
        if self.lowering:
            self.anim_t = min(1.0, self.anim_t + 0.02)
        else:
            self.anim_t = max(0.0, self.anim_t - 0.01)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        margin = 28
        cyl_w = int(w * 0.42)
        cyl_h = int(h * 0.70)
        cyl_x = margin
        cyl_y = margin + 18

        # Идиш
        p.setPen(QPen(Qt.black, 2))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(cyl_x, cyl_y, cyl_w, cyl_h, 8, 8)

        inner_x = cyl_x + 8
        inner_y = cyl_y + 8
        inner_w = cyl_w - 16
        inner_h = cyl_h - 16

        # Суу деңгээли
        water_fill = 0.60
        water_h = inner_h * water_fill
        water_y = inner_y + inner_h - water_h

        # Суу жана толкундар
        path = QPainterPath()
        left = inner_x; right = inner_x + inner_w; bottom = inner_y + inner_h
        steps = 60
        wave_ampl = 3.0 + 3.0 * self.anim_t
        level_y = water_y
        path.moveTo(left, bottom)
        for i in range(steps + 1):
            t = i / steps
            x = left + t * inner_w
            phase = self.wave_phase + t * 2 * math.pi
            y = level_y + math.sin(phase) * (wave_ampl * (1 - abs(2*t-1)))
            path.lineTo(x, y)
        path.lineTo(right, bottom)
        path.closeSubpath()

        if self.t_final is None:
            mix_temp = (self.t1 + self.t2) / 2.0
        else:
            mix_temp = self.t_final
        base_blue = max(60, 255 - int(mix_temp))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(100 + int(mix_temp), 150, base_blue, 220))
        p.drawPath(path)

        p.setPen(QPen(QColor(40,80,160,200), 1))
        p.drawLine(left, level_y, right, level_y)

        # Бөлүктөр
        p.setPen(QPen(Qt.black, 1))
        p.setFont(QFont("Sans", 9))
        for i in range(0, 6):
            y_tick = inner_y + inner_h - i * inner_h / 5
            p.drawLine(inner_x - 10, y_tick, inner_x, y_tick)

        # Цилиндр (ысык нерсе)
        radius_px = max(12, min(int((self.m2 ** (1/3.0)) * 2.0), int(inner_w * 0.40)))
        body_cx = inner_x + inner_w / 2
        top_anchor_y = cyl_y - 24
        
        y_top = top_anchor_y + 16
        y_bottom = level_y + radius_px * 0.6 
        cy = y_top + (y_bottom - y_top) * self.anim_t

        # Жип
        p.setPen(QPen(Qt.black, 1))
        p.drawLine(body_cx, top_anchor_y, body_cx, cy - radius_px)
        
        # Нерсе
        p.setBrush(QColor(200, 90, 70))
        p.setPen(QPen(Qt.black, 1))
        p.drawEllipse(QPointF(body_cx, cy), radius_px, radius_px)
        
        # Термометр
        therm_x = inner_x + inner_w + 24
        therm_y = inner_y + 12
        p.setPen(QPen(Qt.black, 2))
        p.setBrush(QColor(240,240,240))
        p.drawRoundedRect(therm_x, therm_y, 140, 80, 6, 6)
        p.setPen(QPen(Qt.black,1))
        p.setFont(QFont("Sans", 12, QFont.Bold))
        T_show = self.t_final if self.t_final is not None else None
        text = f"T = {T_show:.1f} °C" if T_show is not None else "T = — °C"
        p.drawText(therm_x + 12, therm_y + 46, text)

        # Параметрлерди жазуу
        p.setFont(QFont("Sans", 10))
        p.drawText(therm_x, therm_y + 100, f"m1={self.m1:.0f} г, t1={self.t1:.0f} °C")
        p.drawText(therm_x, therm_y + 116, f"m2={self.m2:.0f} г, t2={self.t2:.0f} °C")
        p.drawText(therm_x, therm_y + 132, f"c1={self.c1:.2f} Дж/(г·°C)")

class LabCmpHeatApp(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Сравнительная теплоёмкость твёрдых тел -> Катуу нерселердин салыштырмалуу жылуулук сыйымдуулугу
        self.setWindowTitle("Лабораториялык иш — Катуу нерселердин салыштырмалуу жылуулук сыйымдуулугу")
        self.setMinimumSize(1100, 680)

        self._generate_experiment()

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.cal = CalorimeterWidget()
        self.cal.set_params(self.m1, self.t1, self.m2, self.t2, C_WATER)
        left.addWidget(self.cal)

        # КОТОРМО: Заголовок
        right.addWidget(QLabel("<b>Катуу нерселердин салыштырмалуу жылуулук сыйымдуулугу</b>"))
        
        # КОТОРМО: Инструкция
        info = QLabel(
            "Ысык цилиндрди сууга түшүрүңүз («Цилиндрди салуу» баскычы), андан кийин «Аралаштыруу» баскычын басыңыз.\n"
            "Акыркы температураны (T) өлчөп, c₂ маанисин формула боюнча эсептеңиз:\n"
            "c₂ = (c₁·m₁·(T − t₁)) / (m₂·(t₂ − T)). Бирдиги: Дж/(г·°C)."
        )
        info.setWordWrap(True)
        right.addWidget(info)

        # Поля ввода
        right.addWidget(QLabel("<b>Тажрыйбанын параметрлери</b>"))
        self.input_m1 = QLineEdit(); self.input_m1.setPlaceholderText("m1 (г) суу")
        self.input_t1 = QLineEdit(); self.input_t1.setPlaceholderText("t1 (°C) суу")
        self.input_m2 = QLineEdit(); self.input_m2.setPlaceholderText("m2 (г) цилиндр")
        self.input_t2 = QLineEdit(); self.input_t2.setPlaceholderText("t2 (°C) цилиндр")
        self.input_c1 = QLineEdit(); self.input_c1.setPlaceholderText("c1 суу (Дж/(г·°C))")
        self.input_c1.setText(f"{C_WATER:.2f}")
        
        right.addWidget(self.input_m1)
        right.addWidget(self.input_t1)
        right.addWidget(self.input_m2)
        right.addWidget(self.input_t2)
        right.addWidget(self.input_c1)

        right.addSpacing(8)
        # КОТОРМО: Ответ ученика -> Окуучунун жообу
        right.addWidget(QLabel("<b>Окуучунун жообу</b>"))
        self.input_T = QLineEdit(); self.input_T.setPlaceholderText("T (°C) — акыркы температура")
        self.input_c2 = QLineEdit(); self.input_c2.setPlaceholderText("c2 (Дж/(г·°C)) — эсептеп көрүңүз")
        right.addWidget(self.input_T)
        right.addWidget(self.input_c2)

        # Кнопки
        # КОТОРМО: Погрузить цилиндр -> Цилиндрди салуу
        btn_lower = QPushButton("Цилиндрди салуу")
        btn_lower.clicked.connect(self.lower_cylinder)
        # КОТОРМО: Смешать -> Аралаштыруу
        btn_mix = QPushButton("Аралаштыруу")
        btn_mix.clicked.connect(self.mix)
        # КОТОРМО: Проверить c2 -> c2 текшерүү
        btn_check = QPushButton("c2 текшерүү")
        btn_check.clicked.connect(self.check_c2)
        # КОТОРМО: Показать правильные значения -> Туура маанилерди көрсөтүү
        btn_show = QPushButton("Туура маанилерди көрсөтүү")
        btn_show.clicked.connect(self.show_answers)
        # КОТОРМО: Случайный эксперимент -> Кокустан тандалган тажрыйба
        btn_random = QPushButton("Кокустан тандалган тажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        # КОТОРМО: Сброс -> Кайра баштоо
        btn_reset = QPushButton("Кайра баштоо")
        btn_reset.clicked.connect(self.reset)

        right.addWidget(btn_lower)
        right.addWidget(btn_mix)
        right.addWidget(btn_check)
        right.addWidget(btn_show)
        right.addWidget(btn_random)
        right.addWidget(btn_reset)

        self.lbl_result = QLabel("")
        right.addWidget(self.lbl_result)
        right.addStretch(1)

        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_labels)
        self.ui_timer.start(200)

    def _generate_experiment(self):
        self.m1 = random.randint(80, 200)   # г суу
        self.t1 = random.randint(15, 30)    # °C
        self.m2 = random.randint(60, 200)   # г цилиндр
        self.t2 = random.randint(60, 95)    # °C
        self.c2_true = random.uniform(0.2, 1.0) # жашыруун c2

    def update_labels(self):
        pass

    def lower_cylinder(self):
        self.cal.start_lowering()

    def mix(self):
        try:
            m1 = float(self.input_m1.text()); t1 = float(self.input_t1.text())
            m2 = float(self.input_m2.text()); t2 = float(self.input_t2.text())
            c1 = float(self.input_c1.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "Сан маанилерин киргизиңиз (m1, t1, m2, t2, c1).")
            return
        self.cal.set_params(m1, t1, m2, t2, c1)
        self.cal.c2_true = self.c2_true
        self.cal.mix()
        if self.cal.t_final is None:
            QMessageBox.information(self, "Маалымат", "Параметрлер туура эмес.")
        else:
            self.input_T.setText(f"{self.cal.t_final:.2f}")

    def check_c2(self):
        if self.cal.t_final is None:
            QMessageBox.information(self, "Маалымат", "Адегенде аралаштырып, T маанисин алыңыз.")
            return
        try:
            c2_user = float(self.input_c2.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "c2 үчүн сан маанисин киргизиңиз.")
            return
        c2_true = float(self.c2_true)
        tol = max(0.05 * c2_true, 0.02)
        if abs(c2_user - c2_true) <= tol:
            # КОТОРМО: ... верно -> ... туура эсептелди
            self.lbl_result.setText("✅ c₂ туура эсептелди.")
        else:
            # КОТОРМО: Неверно... -> Туура эмес...
            self.lbl_result.setText(f"❌ Туура эмес. Туура c₂ ≈ {c2_true:.3f} Дж/(г·°C) ( piela ±{tol:.3f}).")

    def show_answers(self):
        if self.cal.t_final is None:
            QMessageBox.information(self, "Маалымат", "Адегенде аралаштырыңыз.")
            return
        self.input_T.setText(f"{self.cal.t_final:.2f}")
        self.input_c2.setText(f"{self.c2_true:.3f}")
        self.lbl_result.setText("Туура T жана c₂ көрсөтүлдү.")

    def random_experiment(self):
        self._generate_experiment()
        self.input_m1.setText(f"{self.m1:.0f}")
        self.input_t1.setText(f"{self.t1:.0f}")
        self.input_m2.setText(f"{self.m2:.0f}")
        self.input_t2.setText(f"{self.t2:.0f}")
        self.input_c1.setText(f"{C_WATER:.2f}")
        self.cal.set_params(self.m1, self.t1, self.m2, self.t2, C_WATER)
        self.cal.c2_true = self.c2_true
        self.cal.t_final = None
        self.lbl_result.setText("")
        self.input_T.clear(); self.input_c2.clear()

    def reset(self):
        self.input_m1.clear(); self.input_t1.clear()
        self.input_m2.clear(); self.input_t2.clear()
        self.input_c1.setText(f"{C_WATER:.2f}")
        self.input_T.clear(); self.input_c2.clear()
        self.cal.set_params(100, 20, 100, 90, C_WATER)
        self.cal.t_final = None
        self.lbl_result.setText("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabCmpHeatApp()
    win.show()
    sys.exit(app.exec())