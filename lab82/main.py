# lab_cmp_heat.py
# Требуется: pip install PySide6
import sys, random, math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PySide6.QtCore import Qt, QTimer, QPointF

# Принятые школьные единицы:
# масса — граммы (г), температура — °C, теплоёмкость — Дж/(г·°C)
C_WATER = 4.2  # c1 воды, Дж/(г·°C)

class CalorimeterWidget(QFrame):
    """
    Визуализация калориметра с водой и горячим цилиндром.
    Анимация опускания цилиндра в воду. Термометр показывает итоговую T.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(460, 420)
        # параметры воды и цилиндра
        self.m1 = 100.0   # г
        self.t1 = 20.0    # °C
        self.c1 = C_WATER
        self.m2 = 100.0   # г
        self.t2 = 90.0    # °C
        self.t_final = None
        # состояние анимации
        self.lowering = False
        self.anim_t = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(30)
        # оформление волн на поверхности воды
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
        # запускаем анимацию опускания цилиндра
        self.lowering = True

    def mix(self):
        """
        Рассчитываем конечную температуру t, предполагая:
        - теплообмен только между водой и телом, теплопотерями пренебрегаем;
        - теплоёмкость воды c1 известна, у тела c2 неизвестна (ученик считает по формуле);
        Для визуализации конечной T используем правило сохранения энергии при c1 для воды
        и равных c для оценки t (как смесь), либо просто показываем t, заданную как
        энергетический баланс воды и тела при некотором c2_истинном (генерируем).
        Здесь мы отобразим t, исходя из энергетического баланса с заданным скрытым c2_true.
        """
        # Сгенерируем скрытое "истинное" c2 тела (разумный диапазон)
        c2_true = getattr(self, "c2_true", None)
        if c2_true is None:
            c2_true = random.uniform(0.2, 1.0)  # Дж/(г·°C)
            self.c2_true = c2_true

        # Энергетический баланс: c1*m1*(t - t1) = c2*m2*(t2 - t)
        # => t*(c1*m1 + c2*m2) = c1*m1*t1 + c2*m2*t2
        denom = (self.c1 * self.m1 + c2_true * self.m2)
        if denom <= 1e-9:
            self.t_final = None
        else:
            self.t_final = (self.c1 * self.m1 * self.t1 + c2_true * self.m2 * self.t2) / denom
        # запускаем короткую "остывающую" анимацию волн
        self.lowering = False
        self.anim_t = 1.0
        self.update()

    def on_timer(self):
        # волны на поверхности
        self.wave_phase += 0.10
        if self.wave_phase > 2 * math.pi:
            self.wave_phase -= 2 * math.pi
        # анимация опускания цилиндра
        if self.lowering:
            self.anim_t = min(1.0, self.anim_t + 0.02)
        else:
            # лёгкая релаксация волн после смешивания
            self.anim_t = max(0.0, self.anim_t - 0.01)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        # сосуд
        margin = 28
        cyl_w = int(w * 0.42)
        cyl_h = int(h * 0.70)
        cyl_x = margin
        cyl_y = margin + 18

        p.setPen(QPen(Qt.black, 2))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(cyl_x, cyl_y, cyl_w, cyl_h, 8, 8)

        inner_x = cyl_x + 8
        inner_y = cyl_y + 8
        inner_w = cyl_w - 16
        inner_h = cyl_h - 16

        # уровень воды (берём 60% высоты для вида)
        water_fill = 0.60
        water_h = inner_h * water_fill
        water_y = inner_y + inner_h - water_h

        # жидкость + волны
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

        # цвет воды зависит от итоговой температуры (тёплее — чуть краснее)
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

        # деления уровня (подписи объём условно)
        p.setPen(QPen(Qt.black, 1))
        p.setFont(QFont("Sans", 9))
        for i in range(0, 6):
            y_tick = inner_y + inner_h - i * inner_h / 5
            p.drawLine(inner_x - 10, y_tick, inner_x, y_tick)

        # цилиндр (горячий) — анимация опускания
        # радиус по массе тела (кубический корень для пропорциональности)
        radius_px = max(12, min(int((self.m2 ** (1/3.0)) * 2.0), int(inner_w * 0.40)))
        body_cx = inner_x + inner_w / 2
        top_anchor_y = cyl_y - 24
        # позиция цилиндра: сверху -> до погружения -> в воде
        y_top = top_anchor_y + 16
        y_bottom = level_y + radius_px * 0.6  # слегка ниже уровня
        cy = y_top + (y_bottom - y_top) * self.anim_t

        # нитка
        p.setPen(QPen(Qt.black, 1))
        p.drawLine(body_cx, top_anchor_y, body_cx, cy - radius_px)
        # сам цилиндр
        p.setBrush(QColor(200, 90, 70))
        p.setPen(QPen(Qt.black, 1))
        p.drawEllipse(QPointF(body_cx, cy), radius_px, radius_px)
        # лёгкий голубой слой поверх, когда цилиндр в воде
        if self.anim_t >= 0.99:
            p.setBrush(QColor(100, 150, 255, 70))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(body_cx, cy), radius_px, radius_px)

        # термометр (плашка справа)
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

        # подписи параметров
        p.setFont(QFont("Sans", 10))
        p.drawText(therm_x, therm_y + 100, f"m1={self.m1:.0f} г, t1={self.t1:.0f} °C")
        p.drawText(therm_x, therm_y + 116, f"m2={self.m2:.0f} г, t2={self.t2:.0f} °C")
        p.drawText(therm_x, therm_y + 132, f"c1={self.c1:.2f} Дж/(г·°C)")

class LabCmpHeatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная — Сравнительная теплоёмкость твёрдых тел")
        self.setMinimumSize(1100, 680)

        # генерация начального эксперимента
        self._generate_experiment()

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        self.cal = CalorimeterWidget()
        self.cal.set_params(self.m1, self.t1, self.m2, self.t2, C_WATER)
        left.addWidget(self.cal)

        right.addWidget(QLabel("<b>Сравнительная теплоёмкость твёрдых тел</b>"))
        info = QLabel(
            "Опустите горячий цилиндр в воду (кнопка «Погрузить цилиндр»), затем нажмите «Смешать».\n"
            "Измерьте конечную температуру T и вычислите c₂ по формуле:\n"
            "c₂ = (c₁·m₁·(T − t₁)) / (m₂·(t₂ − T)). Единицы: Дж/(г·°C)."
        )
        info.setWordWrap(True)
        right.addWidget(info)

        # поля ввода
        right.addWidget(QLabel("<b>Параметры эксперимента</b>"))
        self.input_m1 = QLineEdit(); self.input_m1.setPlaceholderText("m1 (г) вода")
        self.input_t1 = QLineEdit(); self.input_t1.setPlaceholderText("t1 (°C) вода")
        self.input_m2 = QLineEdit(); self.input_m2.setPlaceholderText("m2 (г) цилиндр")
        self.input_t2 = QLineEdit(); self.input_t2.setPlaceholderText("t2 (°C) цилиндр")
        self.input_c1 = QLineEdit(); self.input_c1.setPlaceholderText("c1 воды (Дж/(г·°C))")
        self.input_c1.setText(f"{C_WATER:.2f}")
        right.addWidget(self.input_m1)
        right.addWidget(self.input_t1)
        right.addWidget(self.input_m2)
        right.addWidget(self.input_t2)
        right.addWidget(self.input_c1)

        right.addSpacing(8)
        right.addWidget(QLabel("<b>Ответ ученика</b>"))
        self.input_T = QLineEdit(); self.input_T.setPlaceholderText("T (°C) — конечная температура")
        self.input_c2 = QLineEdit(); self.input_c2.setPlaceholderText("c2 (Дж/(г·°C)) — рассчитайте сами")
        right.addWidget(self.input_T)
        right.addWidget(self.input_c2)

        # кнопки управления
        btn_lower = QPushButton("Погрузить цилиндр")
        btn_lower.clicked.connect(self.lower_cylinder)
        btn_mix = QPushButton("Смешать")
        btn_mix.clicked.connect(self.mix)
        btn_check = QPushButton("Проверить c2")
        btn_check.clicked.connect(self.check_c2)
        btn_show = QPushButton("Показать правильные значения")
        btn_show.clicked.connect(self.show_answers)
        btn_random = QPushButton("Случайный эксперимент")
        btn_random.clicked.connect(self.random_experiment)
        btn_reset = QPushButton("Сброс")
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

        # UI таймер для обновления (если нужно)
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_labels)
        self.ui_timer.start(200)

    def _generate_experiment(self):
        self.m1 = random.randint(80, 200)   # г воды
        self.t1 = random.randint(15, 30)    # °C
        self.m2 = random.randint(60, 200)   # г цилиндр
        self.t2 = random.randint(60, 95)    # °C
        # скрытое истинное c2 тела
        self.c2_true = random.uniform(0.2, 1.0)

    def update_labels(self):
        # Ничего особого, оставим для будущих подсказок
        pass

    def lower_cylinder(self):
        # запускаем анимацию опускания
        self.cal.start_lowering()

    def mix(self):
        # обновим параметры из полей
        try:
            m1 = float(self.input_m1.text()); t1 = float(self.input_t1.text())
            m2 = float(self.input_m2.text()); t2 = float(self.input_t2.text())
            c1 = float(self.input_c1.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовые значения m1, t1, m2, t2, c1.")
            return
        self.cal.set_params(m1, t1, m2, t2, c1)
        # передадим скрытое истинное c2 в виджет для расчёта T
        self.cal.c2_true = self.c2_true
        self.cal.mix()
        if self.cal.t_final is None:
            QMessageBox.information(self, "Инфо", "Параметры некорректны. Проверьте ввод.")
        else:
            self.input_T.setText(f"{self.cal.t_final:.2f}")

    def check_c2(self):
        # проверка введённого учеником c2 против скрытого истинного
        if self.cal.t_final is None:
            QMessageBox.information(self, "Инфо", "Сначала смешайте и получите T.")
            return
        try:
            c2_user = float(self.input_c2.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовое значение c2.")
            return
        c2_true = float(self.c2_true)
        tol = max(0.05 * c2_true, 0.02)  # 5% или минимум 0.02 Дж/(г·°C)
        if abs(c2_user - c2_true) <= tol:
            self.lbl_result.setText("✅ c₂ рассчитано верно.")
        else:
            self.lbl_result.setText(f"❌ Неверно. Правильное c₂ ≈ {c2_true:.3f} Дж/(г·°C) (допуск ±{tol:.3f}).")

    def show_answers(self):
        if self.cal.t_final is None:
            QMessageBox.information(self, "Инфо", "Сначала смешайте и получите T.")
            return
        self.input_T.setText(f"{self.cal.t_final:.2f}")
        self.input_c2.setText(f"{self.c2_true:.3f}")
        self.lbl_result.setText("Показаны правильные значения T и c₂.")

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
