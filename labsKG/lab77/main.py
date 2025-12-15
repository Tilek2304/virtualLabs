# lab_archimedes.py
# Требуется: pip install PySide6
import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PySide6.QtCore import Qt, QTimer, QPointF

G = 9.81  # м/с^2
RHO_WATER = 1.0  # г/мл (школьные единицы)

# ---------------------------
# Виджет мензурки (уровень жидкости) с видимым телом
# ---------------------------
class MenzurkaWidget(QFrame):
    def __init__(self, total_volume_ml, liquid_volume_ml, divisions, body_volume_ml=0, parent=None):
        super().__init__(parent)
        self.total_volume = total_volume_ml
        self.V_liquid = liquid_volume_ml
        self.divisions = divisions
        self.body_volume = body_volume_ml
        self.body_submerged = False

        self.setMinimumSize(320, 420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(30)

    def on_timer(self):
        self.phase += 0.12
        if self.phase > 2 * math.pi:
            self.phase -= 2 * math.pi
        self.update()

    def set_liquid_volume(self, V):
        self.V_liquid = max(0.0, min(self.total_volume, V))
        self.update()

    def set_body(self, V_body_ml, submerged: bool):
        self.body_volume = V_body_ml
        self.body_submerged = submerged
        self.update()

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

        V_current = self.V_liquid
        liquid_height = inner_h * (V_current / self.total_volume)
        liquid_y = inner_y + inner_h - liquid_height

        # draw liquid with wavy meniscus
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

        # horizontal level line
        painter.setPen(QPen(QColor(40,80,160,200), 1))
        painter.drawLine(left, liquid_y, right, liquid_y)

        # divisions and labels (smaller font)
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

        # draw body: visible either to the right (not submerged) or overlapping liquid (submerged)
        # compute a reasonable radius from volume: scale V (мл) to pixels
        # simple heuristic: radius_px ~ cbrt(V) scaled
        if self.body_volume > 0:
            # cube-root scaling for visual proportionality
            radius_px = max(40, min(int((self.body_volume ** (1/3.0)) * 2.2), int(inner_w * 0.45)))
            body_cx = inner_x + inner_w / 2
            if self.body_submerged:
                # center slightly below surface so body appears immersed
                body_cy = liquid_y + radius_px * 0.6
            else:
                # show body to the right of menzurka (outside) slightly above base
                body_cx = inner_x + inner_w + radius_px + 40
                body_cy = inner_y + inner_h - radius_px - 6
            # draw shadow under body
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0,0,0,40))
            painter.drawEllipse(QPointF(body_cx+3, body_cy+4), radius_px+4, radius_px+4)
            # draw body (solid)
            painter.setBrush(QColor(180,80,80))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawEllipse(QPointF(body_cx, body_cy), radius_px, radius_px)
            # if submerged, draw a faint overlay to show it's under liquid
            if self.body_submerged:
                painter.setBrush(QColor(100,150,255,80))
                painter.setPen(Qt.NoPen)
                # draw a clipped ellipse for the submerged portion (simple visual)
                clip_path = QPainterPath()
                clip_path.addRect(inner_x, inner_y, inner_w, inner_h)
                painter.setClipPath(clip_path)
                painter.drawEllipse(QPointF(body_cx, body_cy), radius_px, radius_px)
                painter.setClipping(False)

        # base
        base_w = int(cyl_w * 0.9)
        base_x = cyl_x + (cyl_w - base_w) // 2
        base_y = cyl_y + cyl_h + 8
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QColor(220,220,220))
        painter.drawRoundedRect(base_x, base_y, base_w, 12, 4, 4)

        # info text
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Sans", max(9, int(w * 0.035)), QFont.Bold))
        painter.drawText(cyl_x, cyl_y - 8, "мл")

# ---------------------------
# Виджет динамометра (цифровой показатель)
# ---------------------------
class DynamometerWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.force_N = 0.0  # текущее показание в ньютонах

    def set_force(self, F):
        self.force_N = F
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width(); h = self.height()
        painter.fillRect(self.rect(), QColor(245,245,245))
        # рамка
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QColor(230,230,230))
        painter.drawRoundedRect(8, 8, w-16, h-16, 6, 6)
        # текст
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Sans", 18, QFont.Bold))
        painter.drawText(20, 40, "Динамометр")
        painter.setFont(QFont("Sans", 20))
        painter.drawText(20, 80, f"{self.force_N:.3f} Н")

# ---------------------------
# Главное приложение (без таблицы)
# ---------------------------
class LabArchimedesApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш — Архимед күчү")
        self.setMinimumSize(1200, 720)

        # генерация эксперимента
        self._generate_experiment()

        # состояние: объект может быть на столе или подвешен и погружён/непогружён
        self.object_attached = False
        self.object_submerged = False

        # GUI
        main_layout = QHBoxLayout(self)
        left_col = QVBoxLayout()
        right_col = QVBoxLayout()
        main_layout.addLayout(left_col, 1)
        main_layout.addLayout(right_col, 0)

        # виджеты слева: мензурка + динамометр
        self.menzurka = MenzurkaWidget(total_volume_ml=self.V_total, liquid_volume_ml=self.V_liquid, divisions=self.N, body_volume_ml=self.V_body)
        self.dynam = DynamometerWidget()
        left_col.addWidget(self.menzurka, 3)
        left_col.addWidget(self.dynam, 0)

        # правая панель: инструкции, поля ввода
        right_col.addWidget(QLabel("<b>Тажрыйба: Архимед күчү</b>"))
        
        # КОТОРМО: Инструкция
        info = QLabel(
            "Абадагы жана суудагы нерсеге таасир эткен күчтү өлчөңүз.\n"
            "F_A = F_аба - F_суу. Теориялык жактан: F_A = ρ·g·V (ρ суу = 1.0 г/мл)."
        )
        info.setWordWrap(True)
        right_col.addWidget(info)

        # КОТОРМО: Состояние -> Абалы, объект на столе -> нерсе үстөлдө
        self.lbl_state = QLabel("Абалы: нерсе үстөлдө")
        # КОТОРМО: F_air -> F_аба, F_water -> F_суу
        self.lbl_readings = QLabel("F_аба = — Н\nF_суу = — Н\nV (мл) = —")
        
        right_col.addWidget(self.lbl_state)
        right_col.addWidget(self.lbl_readings)

        # Поля ввода
        right_col.addSpacing(6)
        # КОТОРМО: Ввод результатов -> Жыйынтыктарды киргизүү
        right_col.addWidget(QLabel("<b>Жыйынтыктарды киргизүү</b>"))
        
        self.input_Fair = QLineEdit()
        self.input_Fair.setPlaceholderText("F_аба маанисин киргизиңиз, Н")
        
        self.input_Fwater = QLineEdit()
        self.input_Fwater.setPlaceholderText("F_суу маанисин киргизиңиз, Н")
        
        self.input_FA = QLineEdit()
        self.input_FA.setPlaceholderText("F_A = F_аба - F_суу маанисин киргизиңиз, Н")
        
        self.input_V = QLineEdit()
        self.input_V.setPlaceholderText("V маанисин киргизиңиз, мл")
        
        right_col.addWidget(self.input_Fair)
        right_col.addWidget(self.input_Fwater)
        right_col.addWidget(self.input_FA)
        right_col.addWidget(self.input_V)

        # Кнопки
        # КОТОРМО: Подвесить объект -> Нерсени илүү
        btn_attach = QPushButton("Нерсени илүү")
        btn_attach.clicked.connect(self.toggle_attach)
        # КОТОРМО: Погрузить / Вынуть -> Сууга салуу / Чыгаруу
        btn_immerse = QPushButton("Сууга салуу / Чыгаруу")
        btn_immerse.clicked.connect(self.toggle_submerge)
        # КОТОРМО: Измерить в воздухе -> Абада өлчөө
        btn_measure_air = QPushButton("Абада өлчөө")
        btn_measure_air.clicked.connect(self.measure_air)
        # КОТОРМО: Измерить в воде -> Сууда өлчөө
        btn_measure_water = QPushButton("Сууда өлчөө")
        btn_measure_water.clicked.connect(self.measure_water)
        # КОТОРМО: Проверить -> Текшерүү
        btn_check = QPushButton("Текшерүү")
        btn_check.clicked.connect(self.check_answers)
        # КОТОРМО: Показать правильные значения -> Туура маанилерди көрсөтүү
        btn_show = QPushButton("Туура маанилерди көрсөтүү")
        btn_show.clicked.connect(self.show_answers)
        # КОТОРМО: Случайный эксперимент -> Кокустан тандалган тажрыйба
        btn_random = QPushButton("Кокустан тандалган тажрыйба")
        btn_random.clicked.connect(self.random_experiment)
        # КОТОРМО: Сброс -> Кайра баштоо
        btn_reset = QPushButton("Кайра баштоо")
        btn_reset.clicked.connect(self.reset_experiment)

        right_col.addWidget(btn_attach)
        right_col.addWidget(btn_immerse)
        right_col.addWidget(btn_measure_air)
        right_col.addWidget(btn_measure_water)
        right_col.addWidget(btn_check)
        right_col.addWidget(btn_show)
        right_col.addWidget(btn_random)
        right_col.addWidget(btn_reset)

        right_col.addStretch(1)

        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(200)
        self._update_dynamometer(0.0)
        
    # ---------------------------
    # Генерация и состояние эксперимента
    # ---------------------------
    def _generate_experiment(self):
        # общий объём мензурки 200..800 мл
        self.V_total = random.randint(200, 800)
        self.N = random.choice([10, 20, 50])
        # объём тела (мл) — 5..(V_total/4)
        self.V_body = random.randint(5, max(5, int(self.V_total * 0.2)))
        # начальный уровень жидкости V_liquid так, чтобы вместился объект
        self.V_liquid = random.randint(30, max(40, self.V_total - self.V_body - 10))
        # масса тела (г) — 10..500
        self.mass_body_g = random.randint(10, 500)
        # истинные силы:
        self.F_air_true = (self.mass_body_g / 1000.0) * G
        self.F_A_true = RHO_WATER * G * self.V_body / 1000.0
        self.F_water_true = max(0.0, self.F_air_true - self.F_A_true)

    # ---------------------------
    # UI и логика измерений
    # ---------------------------
    def toggle_attach(self):
        self.object_attached = not self.object_attached
        if not self.object_attached:
            self._update_dynamometer(0.0)
        else:
            if not self.object_submerged:
                self._update_dynamometer(self.F_air_true)
            else:
                self._update_dynamometer(self.F_water_true)
        self._update_ui()

    def toggle_submerge(self):
        if not self.object_attached:
            QMessageBox.information(self, "Инфо", "Бринчи нерсени илгиле")
            return
        self.object_submerged = not self.object_submerged
        if self.object_submerged:
            self.menzurka.set_liquid_volume(self.V_liquid + self.V_body)
            self.menzurka.set_body(self.V_body, submerged=True)
            self._update_dynamometer(self.F_water_true)
        else:
            self.menzurka.set_liquid_volume(self.V_liquid)
            self.menzurka.set_body(self.V_body, submerged=False)
            self._update_dynamometer(self.F_air_true)
        self._update_ui()

    def measure_air(self):
        if not self.object_attached:
            # КОТОРМО: Инфо -> Маалымат
            QMessageBox.information(self, "Маалымат", "Адегенде нерсени динамометрге илиңиз.")
            return
        self._update_dynamometer(self.F_air_true)
        # КОТОРМО: Измерение -> Өлчөө
        QMessageBox.information(self, "Өлчөө", f"Өлчөндү: F_аба = {self.F_air_true:.3f} Н")
        self._update_ui()

    def measure_water(self):
        if not self.object_attached:
            QMessageBox.information(self, "Маалымат", "Адегенде нерсени илип, сууга салыңыз.")
            return
        if not self.object_submerged:
            QMessageBox.information(self, "Маалымат", "Адегенде нерсени сууга салыңыз («Сууга салуу» баскычы).")
            return
        self._update_dynamometer(self.F_water_true)
        QMessageBox.information(self, "Өлчөө", f"Өлчөндү: F_суу = {self.F_water_true:.3f} Н")
        self._update_ui()

    def _update_ui(self):
        # КОТОРМО: подвешен -> илинген, на столе -> үстөлдө
        state_text = "илинген" if self.object_attached else "үстөлдө"
        # КОТОРМО: погружён -> сууда, не погружён -> сууда эмес
        sub_text = "сууда" if self.object_submerged else "сууда эмес"
        self.lbl_state.setText(f"Абалы: нерсе {state_text}, {sub_text}")
        
        if self.object_attached and not self.object_submerged:
            self.dynam.set_force(self.F_air_true)
            self.lbl_readings.setText(f"F_аба = {self.F_air_true:.3f} Н\nF_суу = — Н\nV (мл) = —")
        elif self.object_attached and self.object_submerged:
            self.dynam.set_force(self.F_water_true)
            self.lbl_readings.setText(f"F_аба = {self.F_air_true:.3f} Н\nF_суу = {self.F_water_true:.3f} Н\nV (мл) = {self.V_body}")
        else:
            self.dynam.set_force(0.0)
            self.lbl_readings.setText("F_аба = — Н\nF_суу = — Н\nV (мл) = —")
        
    def _update_dynamometer(self, F):
        self.dynam.set_force(F)
        
    def check_answers(self):
        try:
            user_Fair = float(self.input_Fair.text())
            user_Fwater = float(self.input_Fwater.text())
            user_FA = float(self.input_FA.text())
            user_V = float(self.input_V.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "Бардык талааларга сан маанилерин киргизиңиз.")
            return
        true_Fair = self.F_air_true
        true_Fwater = self.F_water_true
        true_FA = self.F_A_true
        true_V = float(self.V_body)

        tol_F = max(0.01 * max(true_Fair, true_Fwater, 1.0), 0.01)
        tol_V = max(0.5, 0.02 * true_V)

        ok_Fair = abs(user_Fair - true_Fair) <= tol_F
        ok_Fwater = abs(user_Fwater - true_Fwater) <= tol_F
        ok_FA = abs(user_FA - true_FA) <= max(0.02 * true_FA, 0.01)
        ok_V = abs(user_V - true_V) <= tol_V

        lines = []
        if ok_Fair:
            lines.append("✅ F_аба туура эсептелди.")
        else:
            lines.append(f"❌ F_аба туура эмес. Туурасы: {true_Fair:.3f} Н.")
        
        if ok_Fwater:
            lines.append("✅ F_суу туура эсептелди.")
        else:
            lines.append(f"❌ F_суу туура эмес. Туурасы: {true_Fwater:.3f} Н.")
            
        if ok_FA:
            lines.append("✅ F_A (Архимед күчү) туура эсептелди.")
        else:
            lines.append(f"❌ F_A туура эмес. Туурасы: {true_FA:.3f} Н.")
            
        if ok_V:
            lines.append("✅ V (көлөм) туура эсептелди.")
        else:
            lines.append(f"❌ V туура эмес. Туурасы: {true_V:.1f} мл.")

        QMessageBox.information(self, "Текшерүүнүн жыйынтыгы", "\n".join(lines))

    def show_answers(self):
        self.input_Fair.setText(f"{self.F_air_true:.3f}")
        self.input_Fwater.setText(f"{self.F_water_true:.3f}")
        self.input_FA.setText(f"{self.F_A_true:.3f}")
        self.input_V.setText(f"{self.V_body:.2f}")
        QMessageBox.information(self, "Жооптор", "Туура маанилер көрсөтүлдү.")

    def reset_experiment(self):
        # ... (сброс) ...
        self.lbl_readings.setText("F_аба = — Н\nF_суу = — Н\nV (мл) = —")
        self.lbl_state.setText("Абалы: нерсе үстөлдө")

    def random_experiment(self):
        self._generate_experiment()
        # ... (сброс состояния) ...
        QMessageBox.information(self, "Жаңы тажрыйба", f"Жаңы нерсе түзүлдү: V = {self.V_body} мл, m = {self.mass_body_g} г")
# ---------------------------
# Запуск приложения
# ---------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabArchimedesApp()
    win.show()
    sys.exit(app.exec())
