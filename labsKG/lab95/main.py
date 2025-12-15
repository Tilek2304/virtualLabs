import sys
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QFrame,
    QDoubleSpinBox, QMessageBox, QGroupBox, QHeaderView, QComboBox, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QRadialGradient
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF

# --- БАЗОВЫЙ ШАБЛОН ---
class BaseLabWindow(QWidget):
    def __init__(self, title, formula, description):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(1100, 700)
        
        main_layout = QHBoxLayout(self)
        
        # --- ЛЕВАЯ ПАНЕЛЬ ---
        control_panel = QFrame(); control_panel.setFixedWidth(340)
        control_panel.setStyleSheet("background-color: #f5f5f5; border-right: 1px solid #ddd;")
        ctrl_layout = QVBoxLayout(control_panel)
        
        ctrl_layout.addWidget(QLabel(f"<h2>{title}</h2>"))
        formula_lbl = QLabel(f"<div style='background:#eef; padding:10px; border-radius:5px; font-size:16px; color:blue'><b>{formula}</b></div>")
        ctrl_layout.addWidget(formula_lbl)
        desc_lbl = QLabel(description); desc_lbl.setWordWrap(True); ctrl_layout.addWidget(desc_lbl)
        ctrl_layout.addWidget(QLabel("<hr>"))
        
        # КОТОРМО: Параметры источников -> Булактардын параметрлери
        self.inputs_group = QGroupBox("Булактардын параметрлери")
        self.inputs_layout = QVBoxLayout(self.inputs_group)
        ctrl_layout.addWidget(self.inputs_group)
        
        # Блок ответа
        # КОТОРМО: Анализ точки P -> P чекитин анализдөө
        ans_box = QGroupBox("P чекитин анализдөө")
        ans_layout = QVBoxLayout(ans_box)
        
        # КОТОРМО: Рассчитайте разность хода -> Жол айырмасын эсептеңиз (Δd, см)
        ans_layout.addWidget(QLabel("1. Жол айырмасын эсептеңиз (Δd, см):"))
        self.answer_delta = QLineEdit()
        self.answer_delta.setPlaceholderText("|d1 - d2|")
        ans_layout.addWidget(self.answer_delta)
        
        # КОТОРМО: Тип интерференции -> Интерференциянын түрү
        ans_layout.addWidget(QLabel("2. Интерференциянын түрү:"))
        self.combo_type = QComboBox()
        # КОТОРМО: Не выбрано, Максимум (Усиление), Минимум (Гашение), Промежуточное -> Тандалган жок, Максимум (Күчөтүү), Минимум (Басаңдоо), Ортодогу
        self.combo_type.addItems(["Тандалган жок", "Максимум (Күчөтүү)", "Минимум (Басаңдоо)", "Ортодогу маани"])
        ans_layout.addWidget(self.combo_type)
        
        # КОТОРМО: Проверить -> Текшерүү
        self.btn_check = QPushButton("Текшерүү")
        self.btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_check.clicked.connect(self.check_answer)
        ans_layout.addWidget(self.btn_check)
        
        ctrl_layout.addWidget(ans_box); ctrl_layout.addStretch()
        
        # --- ПРАВАЯ ПАНЕЛЬ ---
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel)
        self.visualizer = self.create_visualizer()
        right_layout.addWidget(self.visualizer, stretch=3)
        
        self.table = QTableWidget(0, 4)
        # КОТОРМО: Заголовки таблицы
        self.table.setHorizontalHeaderLabels(["Δd (Сиз)", "Δd (Чыныгы)", "Түрү", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.table, stretch=1)
        
        main_layout.addWidget(control_panel); main_layout.addWidget(right_panel)

    def create_visualizer(self): return QFrame()
    def check_answer(self): pass 
    def setup_inputs(self): pass

# --- ВИЗУАЛИЗАТОР ВОЛНОВОЙ ВАННЫ ---
class RippleTankVisualizer(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #101020; border: 1px solid #555;")
        
        # Физические параметры (в условных см)
        self.dist_S1_S2 = 10.0 # Расстояние между источниками
        self.wavelength = 2.0  # Длина волны
        self.phase_shift = 0.0 # Сдвиг фазы анимации
        
        # Масштаб (пикселей в 1 см)
        self.scale = 20.0 
        
        # Точка детектора (None, пока не кликнули)
        self.detector_pos = None 
        self.d1 = 0.0
        self.d2 = 0.0
        
        self.show_waves = True
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)

    def update_params(self, dist, lam, show_w):
        self.dist_S1_S2 = dist
        self.wavelength = lam
        self.show_waves = show_w
        self.update_detector_calculations()
        self.update()

    def animate(self):
        # Движение волн (фаза меняется от 0 до wavelength)
        self.phase_shift += 0.2
        if self.phase_shift > self.wavelength:
            self.phase_shift -= self.wavelength
        self.update()

    def mousePressEvent(self, event):
        # Установка детектора по клику
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        
        mx = event.position().x()
        my = event.position().y()
        
        # Переводим в физические координаты (см), центр в (0,0)
        phys_x = (mx - cx) / self.scale
        phys_y = (my - cy) / self.scale
        
        self.detector_pos = QPointF(phys_x, phys_y)
        self.update_detector_calculations()
        self.update()

    def update_detector_calculations(self):
        if self.detector_pos is None: return
        
        # Координаты источников
        s1_x = -self.dist_S1_S2 / 2
        s2_x = self.dist_S1_S2 / 2
        
        # Расстояния
        self.d1 = math.sqrt((self.detector_pos.x() - s1_x)**2 + (self.detector_pos.y())**2)
        self.d2 = math.sqrt((self.detector_pos.x() - s2_x)**2 + (self.detector_pos.y())**2)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        
        # Координаты источников на экране
        s1_scr_x = cx - (self.dist_S1_S2 / 2) * self.scale
        s2_scr_x = cx + (self.dist_S1_S2 / 2) * self.scale
        src_y = cy
        
        # 1. Рисуем волны (Концентрические круги)
        if self.show_waves:
            # Максимальный радиус (диагональ экрана)
            max_r_cm = math.sqrt((w/self.scale)**2 + (h/self.scale)**2)
            
            p.setBrush(Qt.NoBrush)
            
            # Рисуем гребни (сплошные линии)
            # Радиус r = n * lambda + phase
            n = 0
            while True:
                r_cm = n * self.wavelength + self.phase_shift
                if r_cm > max_r_cm: break
                r_px = r_cm * self.scale
                
                # Цвет волны (затухает с расстоянием)
                alpha = max(0, 255 - int(r_px / 2))
                if alpha > 0:
                    pen = QPen(QColor(0, 200, 255, alpha), 2)
                    p.setPen(pen)
                    
                    # Круг от S1
                    p.drawEllipse(QPointF(s1_scr_x, src_y), r_px, r_px)
                    # Круг от S2
                    p.drawEllipse(QPointF(s2_scr_x, src_y), r_px, r_px)
                n += 1

        # 2. Рисуем источники
        p.setBrush(QColor("yellow"))
        p.setPen(Qt.black)
        p.drawEllipse(QPointF(s1_scr_x, src_y), 6, 6)
        p.drawEllipse(QPointF(s2_scr_x, src_y), 6, 6)
        
        p.setPen(QColor("white"))
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.drawText(int(s1_scr_x)-10, int(src_y)-15, "S1")
        p.drawText(int(s2_scr_x)-10, int(src_y)-15, "S2")

        # 3. Рисуем Детектор (если выбран)
        if self.detector_pos:
            det_scr_x = cx + self.detector_pos.x() * self.scale
            det_scr_y = cy + self.detector_pos.y() * self.scale
            
            # Линии от источников к детектору
            p.setPen(QPen(QColor("red"), 1, Qt.DashLine))
            p.drawLine(QPointF(s1_scr_x, src_y), QPointF(det_scr_x, det_scr_y))
            p.drawLine(QPointF(s2_scr_x, src_y), QPointF(det_scr_x, det_scr_y))
            
            # Точка
            p.setBrush(QColor("red"))
            p.setPen(Qt.white)
            p.drawEllipse(QPointF(det_scr_x, det_scr_y), 5, 5)
            p.drawText(int(det_scr_x)+10, int(det_scr_y), "P")
            
            # Подписи длин
            mid_x1 = (s1_scr_x + det_scr_x) / 2
            mid_y1 = (src_y + det_scr_y) / 2
            p.drawText(int(mid_x1), int(mid_y1), f"d1={self.d1:.1f}")
            
            mid_x2 = (s2_scr_x + det_scr_x) / 2
            mid_y2 = (src_y + det_scr_y) / 2
            p.drawText(int(mid_x2), int(mid_y2), f"d2={self.d2:.1f}")
        else:
            p.setPen(QColor("white"))
            p.setFont(QFont("Arial", 12))
            # КОТОРМО: Кликните... -> Детекторду коюу үчүн каалаган жерге чыкылдатыңыз.
            p.drawText(20, 30, "Детекторду коюу үчүн каалаган жерге чыкылдатыңыз.")


# --- ЛОГИКА ЛАБОРАТОРНОЙ ---
class InterferenceLab(BaseLabWindow):
    def __init__(self):
        super().__init__(
            # КОТОРМО: 9 Класс: Интерференция волн -> 9-класс: Толкундардын интерференциясы
            title="9-класс: Толкундардын интерференциясы",
            formula="Δd = kλ (Макс)  |  Δd = (k + 0.5)λ (Мин)",
            description=(
                # КОТОРМО: Цель -> Максаты, Инструкция
                "<b>Максаты:</b> Толкундардын күчөтүлүү жана басаңдоо шарттарын изилдөө.<br>"
                "1. Булактардын параметрлерин орнотуңуз.<br>"
                "2. <b>Талаага чыкылдатып</b>, P чекитин тандаңыз.<br>"
                "3. Сизге d1 жана d2 аралыктары берилет. Жол айырмасын Δd эсептеңиз.<br>"
                "4. Δd менен толкун узундугу λ-ны салыштырып, Максимум же Минимум экенин аныктаңыз."
            )
        )
        self.setup_inputs()

    def create_visualizer(self):
        return RippleTankVisualizer()

    def setup_inputs(self):
        # КОТОРМО: Расстояние S1-S2 -> S1-S2 аралыгы
        self.inputs_layout.addWidget(QLabel("S1-S2 аралыгы (см):"))
        self.spin_dist = QDoubleSpinBox()
        self.spin_dist.setRange(2.0, 30.0)
        self.spin_dist.setValue(10.0)
        self.inputs_layout.addWidget(self.spin_dist)
        
        # КОТОРМО: Длина волны -> Толкун узундугу (λ)
        self.inputs_layout.addWidget(QLabel("Толкун узундугу λ (см):"))
        self.spin_lam = QDoubleSpinBox()
        self.spin_lam.setRange(1.0, 10.0)
        self.spin_lam.setValue(2.0)
        self.inputs_layout.addWidget(self.spin_lam)
        
        # КОТОРМО: Показывать волны -> Толкундарды көрсөтүү
        self.chk_waves = QCheckBox("Толкундарды көрсөтүү")
        self.chk_waves.setChecked(True)
        self.inputs_layout.addWidget(self.chk_waves)
        
        self.spin_dist.valueChanged.connect(self.update_vis)
        self.spin_lam.valueChanged.connect(self.update_vis)
        self.chk_waves.stateChanged.connect(self.update_vis)
        
        self.update_vis()

    def update_vis(self):
        self.visualizer.update_params(
            self.spin_dist.value(),
            self.spin_lam.value(),
            self.chk_waves.isChecked()
        )

    def check_answer(self):
        if self.visualizer.detector_pos is None:
            # КОТОРМО: Внимание -> Көңүл буруңуз
            QMessageBox.warning(self, "Көңүл буруңуз", "Адегенде талаага чыкылдатып, өлчөө чекитин тандаңыз!")
            return

        # 1. Проверка числа
        try:
            user_delta = float(self.answer_delta.text().replace(',', '.'))
        except ValueError:
            QMessageBox.warning(self, "Ката", "Жол айырмасын сан түрүндө киргизиңиз.")
            return
            
        true_delta = abs(self.visualizer.d1 - self.visualizer.d2)
        lam = self.spin_lam.value()
        
        # Погрешность 0.1 см
        is_val_correct = abs(user_delta - true_delta) <= 0.1
        
        # 2. Проверка типа интерференции
        ratio = true_delta / (lam / 2.0)
        closest_integer = round(ratio)
        deviation = abs(ratio - closest_integer)
        
        # Определяем "истинный" тип
        if deviation < 0.2: # Достаточно близко к целому полуволн
            if closest_integer % 2 == 0:
                true_type_idx = 1 # Максимум
                # КОТОРМО: Максимум
                type_str = "Максимум"
            else:
                true_type_idx = 2 # Минимум
                # КОТОРМО: Минимум
                type_str = "Минимум"
        else:
            true_type_idx = 3 # Промежуточное
            # КОТОРМО: Ортодогу маани
            type_str = "Ортодогу маани"
            
        user_type_idx = self.combo_type.currentIndex()
        is_type_correct = (user_type_idx == true_type_idx)
        is_total_correct = is_val_correct and is_type_correct
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(f"{user_delta:.2f}"))
        self.table.setItem(row, 1, QTableWidgetItem(f"{true_delta:.2f}"))
        self.table.setItem(row, 2, QTableWidgetItem(type_str))
        
        status_item = QTableWidgetItem("✅ Туура" if is_total_correct else "❌ Ката")
        status_item.setForeground(QBrush(QColor("green") if is_total_correct else QColor("red")))
        self.table.setItem(row, 3, status_item)
        
        if is_total_correct:
            QMessageBox.information(self, "Азаматсыз", f"Туура! Δd={true_delta:.2f} см ≈ {true_delta/lam:.1f}λ -> {type_str}")
        else:
            msg = []
            if not is_val_correct: msg.append(f"Δd эсебинде ката. Туура: {true_delta:.2f}")
            if not is_type_correct: msg.append(f"Интерференциянын түрү туура эмес. Бул {type_str}.")
            QMessageBox.warning(self, "Ката", "\n".join(msg))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = InterferenceLab()
    window.show()
    sys.exit(app.exec())