# lab_spectra.py
# Требуется: pip install PySide6
import sys, math, random
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QComboBox, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient
from PySide6.QtCore import Qt, QTimer

# --- Наборы линий для разных ламп (в нанометрах) ---
LAMPS = {
    "Накаливания (лампа накаливания)": {
        "type": "continuous",
        "info": "Непрерывный спектр (широкий диапазон длин волн)."
    },
    "Водород (линейный, Balmer)": {
        "type": "lines",
        "lines": [
            (656.3, "Hα"),
            (486.1, "Hβ"),
            (434.0, "Hγ"),
            (410.2, "Hδ")
        ],
        "info": "Линии Бальмера водорода."
    },
    "Гелий (линейный)": {
        "type": "lines",
        "lines": [
            (587.6, "He 587.6"),
            (501.6, "He 501.6"),
            (447.1, "He 447.1")
        ],
        "info": "Некоторые яркие линии гелия."
    },
    "Ртуть (линейный)": {
        "type": "lines",
        "lines": [
            (546.1, "Hg 546.1"),
            (435.8, "Hg 435.8"),
            (404.7, "Hg 404.7")
        ],
        "info": "Яркие линии ртути."
    }
}

# --- Визуальный виджет спектра ---
class SpectrumWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(820, 220)
        self.lamp_name = "Накаливания (лампа накаливания)"
        self.range_min = 380.0  # nm
        self.range_max = 780.0  # nm
        self.lines = []         # список (wavelength_nm, label)
        self.spectrum_type = "continuous"
        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(80)

    def set_lamp(self, name):
        self.lamp_name = name
        info = LAMPS.get(name, {})
        self.spectrum_type = info.get("type", "continuous")
        self.lines = info.get("lines", [])
        self.update()

    def _animate(self):
        # небольшая пульсация для непрерывного спектра
        self.phase += 0.03
        if self.phase > 2*math.pi:
            self.phase -= 2*math.pi
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(18, 18, 20))

        # рисуем шкалу длин волн внизу
        margin = 20
        left = margin; right = w - margin
        top = 12; bottom = h - 28
        width = right - left

        # непрерывный спектр: градиент от 380..780 nm
        if self.spectrum_type == "continuous":
            grad = QLinearGradient(left, top, right, top)
            # создаём градиент по видимому спектру (приближённо)
            def nm_to_qcolor(nm):
                # приближённое отображение nm -> RGB
                nm = float(nm)
                r = g = b = 0.0
                if 380 <= nm < 440:
                    r = -(nm - 440) / (440 - 380)
                    g = 0.0
                    b = 1.0
                elif 440 <= nm < 490:
                    r = 0.0
                    g = (nm - 440) / (490 - 440)
                    b = 1.0
                elif 490 <= nm < 510:
                    r = 0.0
                    g = 1.0
                    b = -(nm - 510) / (510 - 490)
                elif 510 <= nm < 580:
                    r = (nm - 510) / (580 - 510)
                    g = 1.0
                    b = 0.0
                elif 580 <= nm < 645:
                    r = 1.0
                    g = -(nm - 645) / (645 - 580)
                    b = 0.0
                elif 645 <= nm <= 780:
                    r = 1.0
                    g = 0.0
                    b = 0.0
                # интенсивность коррекция
                if 380 <= nm < 420:
                    factor = 0.3 + 0.7*(nm - 380)/(420 - 380)
                elif 420 <= nm <= 700:
                    factor = 1.0
                else:
                    factor = 0.3 + 0.7*(780 - nm)/(780 - 700)
                r = max(0.0, min(1.0, r * factor))
                g = max(0.0, min(1.0, g * factor))
                b = max(0.0, min(1.0, b * factor))
                return QColor(int(r*255), int(g*255), int(b*255))
            # add gradient stops
            steps = 24
            for i in range(steps+1):
                nm = self.range_min + (self.range_max - self.range_min) * (i/steps)
                pos = left + width * (i/steps)
                grad.setColorAt(i/steps, nm_to_qcolor(nm))
            p.setBrush(grad)
            p.setPen(Qt.NoPen)
            p.drawRect(left, top, width, bottom - top)
            # subtle shimmer
            shimmer = int(6 * math.sin(self.phase))
            p.setPen(QPen(QColor(255,255,255,20), 1))
            for i in range(0, width, 40):
                p.drawLine(left + i + shimmer, top, left + i + shimmer, bottom)
        else:
            # рисуем тёмный фон полос и тонкую подсветку
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(30,30,40))
            p.drawRect(left, top, width, bottom - top)
            # рисуем линии как яркие вертикальные полосы
            for wl, label in self.lines:
                # позиция по шкале
                frac = (wl - self.range_min) / (self.range_max - self.range_min)
                x = left + int(frac * width)
                # яркость по порядку
                brightness = 220
                color = QColor(255, 220, 80, brightness)
                p.setPen(Qt.NoPen); p.setBrush(color)
                p.drawRect(x-2, top, 6, bottom - top)
                # тонкая ореола
                p.setPen(QPen(QColor(255,200,120,80), 1))
                p.drawLine(x-8, top+6, x+8, top+6)

        # шкала и подписи длин волн
        p.setPen(QPen(Qt.white,1)); p.setFont(QFont("Sans",9))
        for nm in range(380, 781, 40):
            frac = (nm - self.range_min) / (self.range_max - self.range_min)
            x = left + int(frac * width)
            p.drawLine(x, bottom, x, bottom+6)
            p.drawText(x-18, bottom+20, f"{nm} nm")

        # подписи текущей лампы
        p.setPen(QPen(Qt.white,1)); p.setFont(QFont("Sans",10,QFont.Bold))
        p.drawText(12, 18, f"Лампа: {self.lamp_name}")
        info = LAMPS.get(self.lamp_name, {}).get("info", "")
        p.setFont(QFont("Sans",9)); p.drawText(12, 36, info)

# --- Главное приложение ---
class LabSpectraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Спектры — спектроскоп (линейные и непрерывные)")
        self.setMinimumSize(1100, 640)

        main = QHBoxLayout(self)
        left = QVBoxLayout(); right = QVBoxLayout()
        main.addLayout(left, 2); main.addLayout(right, 1)

        # виджет спектра
        self.spectrum = SpectrumWidget()
        left.addWidget(self.spectrum)

        # правая панель: выбор лампы и поля ученика
        right.addWidget(QLabel("<b>Выбор источника</b>"))
        self.combo_lamp = QComboBox()
        for name in LAMPS.keys():
            self.combo_lamp.addItem(name)
        self.combo_lamp.currentTextChanged.connect(self.on_lamp_change)
        right.addWidget(self.combo_lamp)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Режим</b>"))
        self.chk_manual = QCheckBox("Ручной режим (ученик сам записывает наблюдения)")
        right.addWidget(self.chk_manual)

        right.addSpacing(6)
        right.addWidget(QLabel("<b>Поля ученика (введите наблюдения)</b>"))
        # для линейных спектров — список линий (ввод одной линии для проверки)
        self.input_wl = QLineEdit(); self.input_wl.setPlaceholderText("λ (nm) — измеренная длина волны или центр линии")
        self.input_label = QLineEdit(); self.input_label.setPlaceholderText("Метка линии (например Hα)")
        self.input_comment = QLineEdit(); self.input_comment.setPlaceholderText("Комментарий / тип (опционально)")
        right.addWidget(self.input_wl)
        right.addWidget(self.input_label)
        right.addWidget(self.input_comment)

        # кнопки
        btn_apply = QPushButton("Применить источник")
        btn_apply.clicked.connect(self.apply_lamp)
        btn_measure = QPushButton("Измерить (имитация)")
        btn_measure.clicked.connect(self.measure)
        btn_check = QPushButton("Проверить наблюдение")
        btn_check.clicked.connect(self.check)
        btn_show = QPushButton("Показать правильные линии")
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
        self.lbl_model = QLabel("Модель: —")
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setWordWrap(True)
        right.addWidget(self.lbl_model)
        right.addWidget(self.lbl_feedback)
        right.addStretch(1)

        # стартовые значения
        self.random_example()
        # таймер для обновления UI
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(200)

    def on_lamp_change(self, name):
        self.spectrum.set_lamp(name)
        self._update_ui()

    def apply_lamp(self):
        name = self.combo_lamp.currentText()
        self.spectrum.set_lamp(name)
        self.lbl_feedback.setText("Источник применён. Наблюдайте спектр слева.")
        self._update_ui()

    def measure(self):
        # автоматическое заполнение (имитация) — только если не ручной режим
        if self.chk_manual.isChecked():
            self.lbl_feedback.setText("Ручной режим: поля не заполняются автоматически.")
            return
        lamp = self.combo_lamp.currentText()
        info = LAMPS.get(lamp, {})
        if info.get("type") == "continuous":
            # для непрерывного спектра имитируем пик доминирующей длины волны (например цвет лампы)
            peak_nm = random.uniform(500, 3000)  # incandescent broad; but keep visible
            peak_nm = random.uniform(450, 700)
            self.input_wl.setText(f"{peak_nm:.0f}")
            self.input_label.setText("continuous")
            self.lbl_feedback.setText("Непрерывный спектр: записывайте диапазон/цвета, а не отдельные линии.")
        else:
            # выберем случайную линию из набора и добавим шум
            lines = info.get("lines", [])
            if not lines:
                self.lbl_feedback.setText("Нет линий в модели.")
                return
            wl, lab = random.choice(lines)
            wl_meas = wl * (1 + random.uniform(-0.008, 0.008))
            self.input_wl.setText(f"{wl_meas:.1f}")
            self.input_label.setText(lab)
            self.lbl_feedback.setText("Поля заполнены имитацией наблюдения (с небольшой погрешностью).")
        self._update_ui()

    def check(self):
        # проверка: для линейных спектров — сравнить введённую длину волны с ближайшей модельной линией
        lamp = self.combo_lamp.currentText()
        info = LAMPS.get(lamp, {})
        try:
            wl_user = float(self.input_wl.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Введите числовое значение λ (nm).")
            return
        label_user = self.input_label.text().strip()
        if info.get("type") == "continuous":
            # для непрерывного спектра проверяем, что пользователь не пытался указать линию
            if label_user.lower() in ("", "continuous", "непрерывный", "continuous spectrum"):
                self.lbl_feedback.setText("✅ Непрерывный спектр — отдельные линии отсутствуют.")
            else:
                self.lbl_feedback.setText("❌ Непрерывный спектр: нельзя ожидать ярких отдельных линий.")
            return
        # для линейного спектра
        lines = info.get("lines", [])
        # найдем ближайшую модельную линию
        best = None
        best_diff = None
        for wl_model, lab in lines:
            diff = abs(wl_user - wl_model)
            if best is None or diff < best_diff:
                best = (wl_model, lab)
                best_diff = diff
        # допуск: 1% или 1 nm минимум
        tol = max(0.01 * best[0], 1.0)
        ok_wl = best_diff <= tol
        ok_label = (label_user.lower() == best[1].lower()) if label_user else False
        lines_out = []
        if ok_wl:
            lines_out.append(f"✅ λ близко к линии {best[1]} ({best[0]:.1f} nm).")
        else:
            lines_out.append(f"❌ λ не совпадает с ближайшей модельной линией {best[1]} ({best[0]:.1f} nm).")
        if ok_label:
            lines_out.append("✅ Метка линии указана верно.")
        else:
            lines_out.append(f"❌ Метка неверна или отсутствует. Правильно: {best[1]}.")
        self.lbl_feedback.setText("\n".join(lines_out))
        self._update_ui()

    def show_answer(self):
        lamp = self.combo_lamp.currentText()
        info = LAMPS.get(lamp, {})
        if info.get("type") == "continuous":
            self.input_wl.setText("")
            self.input_label.setText("continuous")
            self.lbl_feedback.setText("Непрерывный спектр: нет отдельных линий для показа.")
        else:
            lines = info.get("lines", [])
            if not lines:
                self.lbl_feedback.setText("Нет модельных линий для этой лампы.")
                return
            wl, lab = random.choice(lines)
            self.input_wl.setText(f"{wl:.1f}")
            self.input_label.setText(lab)
            self.lbl_feedback.setText("Показана одна из модельных линий (точное значение).")
        self._update_ui()

    def random_example(self):
        # случайный выбор лампы
        lamp = random.choice(list(LAMPS.keys()))
        self.combo_lamp.setCurrentText(lamp)
        self.spectrum.set_lamp(lamp)
        self.input_wl.clear(); self.input_label.clear(); self.input_comment.clear()
        self.lbl_feedback.setText("Случайный пример: выбрана лампа. Нажмите «Измерить» или наблюдайте спектр.")
        self._update_ui()

    def reset_all(self):
        self.combo_lamp.setCurrentIndex(0)
        self.spectrum.set_lamp(self.combo_lamp.currentText())
        self.input_wl.clear(); self.input_label.clear(); self.input_comment.clear()
        self.lbl_feedback.setText("Сброшено.")
        self._update_ui()

    def _update_ui(self):
        lamp = self.combo_lamp.currentText()
        info = LAMPS.get(lamp, {})
        typ = info.get("type", "—")
        self.lbl_model.setText(f"Модель: {lamp} ({typ})")
        # обновляем виджет спектра
        self.spectrum.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LabSpectraApp()
    win.show()
    sys.exit(app.exec())
