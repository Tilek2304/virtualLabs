import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QHBoxLayout, QFrame, QSizePolicy,
    QGroupBox, QTextEdit
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PySide6.QtCore import Qt, QTimer, QRectF

# ==========================================
# ВИЗУАЛИЗАЦИЯ КЛАССЫ (Мензурка)
# ==========================================
class MenzurkaWidget(QFrame):
    """
    Бөлүктөрү, оң жактагы жазуулары жана суюктуктун анимациясы бар мензурканы чиет.
    """
    def __init__(self, total_volume, liquid_volume, divisions, parent=None):
        super().__init__(parent)
        self.set_parameters(total_volume, liquid_volume, divisions)

        self.setMinimumSize(250, 450)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Виджет үчүн ак фон
        self.setStyleSheet("background-color: white; border: 1px solid #ccc; border-radius: 8px;")

        # Анимация
        self.phase = 0.0
        self.amp_px = 3.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(40)  # ~25 FPS

    def set_parameters(self, total_volume, liquid_volume, divisions):
        """Параметрлерди жаңыртуу"""
        self.total_volume = total_volume
        self.base_liquid = liquid_volume
        self.divisions = divisions
        self.update() # Кайра тартуу

    def on_timer(self):
        self.phase += 0.12
        if self.phase > 2 * math.pi:
            self.phase -= 2 * math.pi
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin_x = int(w * 0.15)
        margin_y = int(h * 0.08)

        cyl_w = int(w * 0.4)
        cyl_h = int(h * 0.8)
        cyl_x = margin_x
        cyl_y = margin_y

        # 1. Корпус (айнек)
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        rect = QRectF(cyl_x, cyl_y, cyl_w, cyl_h)
        painter.drawRoundedRect(rect, 6, 6)

        inner_x = cyl_x + 6
        inner_w = cyl_w - 12
        inner_y = cyl_y + 6
        inner_h = cyl_h - 12

        # 2. Суюктук
        if self.total_volume > 0:
            ratio = self.base_liquid / self.total_volume
        else:
            ratio = 0
            
        base_height_px = inner_h * ratio
        anim_offset = self.amp_px * math.sin(self.phase)
        liquid_height_px = max(0.0, min(inner_h, base_height_px + anim_offset))
        liquid_top_y = inner_y + inner_h - liquid_height_px

        path = QPainterPath()
        left = inner_x
        right = inner_x + inner_w
        bottom = inner_y + inner_h
        
        # Толкундар
        wave_ampl = 4.0 
        path.moveTo(left, bottom)
        path.lineTo(left, liquid_top_y)
        
        steps = 40
        for i in range(steps + 1):
            t = i / steps
            x = left + t * inner_w
            phase = self.phase + t * 2 * math.pi
            y = liquid_top_y + math.sin(phase) * (wave_ampl * (1 - abs(2*t-1)))
            path.lineTo(x, y)
            
        path.lineTo(right, bottom)
        path.closeSubpath()

        painter.setPen(Qt.NoPen)
        # Суюктуктун түсү (көк)
        painter.setBrush(QColor(60, 120, 240, 180))
        painter.drawPath(path)

        # Деңгээл сызыгы
        painter.setPen(QPen(QColor(0, 50, 150, 220), 1, Qt.DashLine))
        painter.drawLine(left, liquid_top_y, right, liquid_top_y)

        # 3. Шкала
        painter.setPen(QPen(Qt.black, 1))
        font_size = max(8, int(w * 0.035))
        painter.setFont(QFont("Segoe UI", font_size))
        
        if self.divisions > 0:
            for i in range(self.divisions + 1):
                t = i / self.divisions
                y_tick = inner_y + inner_h - t * inner_h
                
                # Сызыктарды тартуу
                painter.drawLine(inner_x - 5, y_tick, inner_x + 5, y_tick) # Ичинен солго
                painter.drawLine(inner_x + inner_w - 5, y_tick, inner_x + inner_w + 10, y_tick) # Сыртынан оңго

                # Маанилерди жазуу (окумдуу болуш үчүн)
                step_label = 1
                if self.divisions > 20: step_label = 5
                if self.divisions > 50: step_label = 10
                
                if i % step_label == 0:
                    val = int(round(t * self.total_volume))
                    text = str(val)
                    painter.drawText(inner_x + inner_w + 15, y_tick + 5, text)

        # Төмөнкү "0"
        painter.drawText(inner_x - 15, inner_y + inner_h + 5, "0")

        # 4. Негизи (подставка)
        base_w = int(cyl_w * 0.9)
        base_x = cyl_x + (cyl_w - base_w) // 2
        base_y = cyl_y + cyl_h + 6
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QColor(100, 100, 100))
        painter.drawRoundedRect(base_x, base_y, base_w, 10, 3, 3)

        # "мл" жазуусу
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Segoe UI", font_size + 1, QFont.Bold))
        painter.drawText(cyl_x, cyl_y - 10, "мл")


# ==========================================
# ТИРКЕМЕНИН НЕГИЗГИ ТЕРЕЗЕСИ
# ==========================================
class Lab01App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш №1: Мензурканын бөлүгүнүн баасын аныктоо")
        self.resize(900, 600)
        self.setup_ui()
        self.generate_task() # Биринчи тапшырманы түзүү

    def setup_ui(self):
        # Негизги горизонталдык макет
        main_layout = QHBoxLayout(self)

        # --- СОЛ ЖАК: Визуализация ---
        self.menzurka = MenzurkaWidget(100, 50, 10) 
        
        left_container = QGroupBox("Эксперимент")
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.menzurka)
        left_container.setLayout(left_layout)
        
        main_layout.addWidget(left_container, stretch=3)

        # --- ОҢ ЖАК: Башкаруу ---
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, stretch=2)

        # 1. Тапшырма блогу
        task_group = QGroupBox("Тапшырманын параметрлери")
        task_layout = QVBoxLayout()
        
        self.lbl_info = QLabel("Мензурканын бөлүгүнүн баасын жана суюктуктун учурдагы көлөмүн аныктаңыз.")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setStyleSheet("color: #555; font-style: italic;")
        
        self.lbl_params = QLabel("Параметрлер: ...")
        self.lbl_params.setFont(QFont("Segoe UI", 10, QFont.Bold))
        
        task_layout.addWidget(self.lbl_info)
        task_layout.addWidget(self.lbl_params)
        task_group.setLayout(task_layout)
        right_panel.addWidget(task_group)

        # 2. Маалымат киргизүү блогу
        input_group = QGroupBox("Маалыматтарды киргизүү")
        input_layout = QVBoxLayout()
        
        self.inp_price = QLineEdit()
        self.inp_price.setPlaceholderText("Бөлүктүн баасы (мисалы, 2.5)")
        
        self.inp_volume = QLineEdit()
        self.inp_volume.setPlaceholderText("Суюктуктун көлөмү V (мл)")
        
        input_layout.addWidget(QLabel("Бөлүктүн баасы (С):"))
        input_layout.addWidget(self.inp_price)
        input_layout.addWidget(QLabel("Көлөм (V):"))
        input_layout.addWidget(self.inp_volume)
        input_group.setLayout(input_layout)
        right_panel.addWidget(input_group)

        # 3. Башкаруу баскычтары
        ctrl_group = QGroupBox("Башкаруу")
        ctrl_layout = QVBoxLayout()
        
        # Негизги аракет баскычы
        self.btn_check = QPushButton("Эсептөөлөрдү текшерүү")
        self.btn_check.setMinimumHeight(40)
        self.btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px;")
        self.btn_check.clicked.connect(self.check_answer)
        
        # Кошумча баскычтар
        h_btns = QHBoxLayout()
        
        self.btn_new = QPushButton("Жаңы тапшырма")
        self.btn_new.clicked.connect(self.generate_task)
        self.btn_new.setStyleSheet("background-color: #2196F3; color: white;")
        
        self.btn_clear = QPushButton("Тазалоо")
        self.btn_clear.clicked.connect(self.clear_fields)
        
        h_btns.addWidget(self.btn_new)
        h_btns.addWidget(self.btn_clear)

        ctrl_layout.addWidget(self.btn_check)
        ctrl_layout.addLayout(h_btns)
        ctrl_group.setLayout(ctrl_layout)
        right_panel.addWidget(ctrl_group)

        # 4. Жыйынтыктар (Журнал)
        res_group = QGroupBox("Өлчөө журналы")
        res_layout = QVBoxLayout()
        
        self.txt_result = QTextEdit()
        self.txt_result.setReadOnly(True)
        self.txt_result.setStyleSheet("background-color: #f9f9f9; font-family: Consolas;")
        
        self.btn_copy = QPushButton("Журналды көчүрүү")
        self.btn_copy.clicked.connect(self.copy_log)
        
        res_layout.addWidget(self.txt_result)
        res_layout.addWidget(self.btn_copy)
        res_group.setLayout(res_layout)
        right_panel.addWidget(res_group, stretch=1)
        
        # 5. Чыгуу
        self.btn_exit = QPushButton("Чыгуу")
        self.btn_exit.setStyleSheet("background-color: #f44336; color: white;")
        self.btn_exit.clicked.connect(self.close)
        right_panel.addWidget(self.btn_exit)

    # --- ЛОГИКА ---
    def generate_task(self):
        """Жаңы кокустук шарттарды түзүү"""
        # Толук көлөмдөрдүн варианттары
        self.total_v = random.choice([50, 100, 200, 250, 500, 1000])
        
        # Бөлүктөрдүн санын тандоо (бөлүктүн баасы ыңгайлуу болушу үчүн)
        options = []
        for n in [10, 20, 25, 50, 100]:
            if self.total_v % n == 0:
                options.append(n)
        
        if not options: options = [10]
        self.num_divs = random.choice(options)
        
        # Чыныгы бөлүнүү баасы
        self.true_price = self.total_v / self.num_divs
        
        # Суюктуктун кокустук көлөмү
        min_v = int(self.total_v * 0.1)
        max_v = int(self.total_v * 0.95)
        step = self.true_price / 2
        
        steps_count = int((max_v - min_v) / step)
        self.current_v = min_v + random.randint(0, steps_count) * step

        # UI жаңыртуу
        self.menzurka.set_parameters(self.total_v, self.current_v, self.num_divs)
        self.lbl_params.setText(f"Макс. көлөм: {self.total_v} мл | Бөлүктөр: {self.num_divs}")
        
        # Талааларды тазалоо, бирок журналды эмес
        self.clear_fields()
        self.txt_result.append(f"--- Жаңы тапшырма: Vmax={self.total_v}, N={self.num_divs} ---")

    def check_answer(self):
        """Колдонуучунун жоопторун текшерүү"""
        p_text = self.inp_price.text().replace(',', '.')
        v_text = self.inp_volume.text().replace(',', '.')

        # 1. Валидация
        if not p_text or not v_text:
            QMessageBox.critical(self, "Ката", "Сураныч, эки талааны тең толтуруңуз (Бөлүктүн баасы жана Көлөм).")
            return

        try:
            user_price = float(p_text)
            user_vol = float(v_text)
        except ValueError:
            QMessageBox.critical(self, "Ката", "Туура эмес маалымат киргизилди. Сандарды гана колдонуңуз.")
            return

        # 2. Текшерүү (жол берилген каталык менен)
        price_ok = abs(user_price - self.true_price) < (self.true_price * 0.01 + 0.001)
        
        vol_tolerance = self.true_price / 2
        vol_ok = abs(user_vol - self.current_v) <= vol_tolerance

        # 3. Жыйынтыкты чыгаруу
        if price_ok and vol_ok:
            result_msg = "✅ ТУУРА"
            color = "green"
        else:
            result_msg = "❌ КАТА"
            color = "red"
            
        self.txt_result.append(f"<span style='color:{color}'><b>{result_msg}</b></span>")
        self.txt_result.append(f"Сиздин жооп: C={user_price}, V={user_vol}")
        
        if not (price_ok and vol_ok):
            self.txt_result.append(f"Туура жооп: C={self.true_price:.1f}, V={self.current_v:.1f}")
        
        self.txt_result.append("-" * 30)
        
        # Төмөн жылдыруу
        sb = self.txt_result.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear_fields(self):
        self.inp_price.clear()
        self.inp_volume.clear()

    def copy_log(self):
        self.txt_result.selectAll()
        self.txt_result.copy()
        cursor = self.txt_result.textCursor()
        cursor.clearSelection()
        self.txt_result.setTextCursor(cursor)
        QMessageBox.information(self, "Көчүрүү", "Журнал буферге көчүрүлдү!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Тиркеменин жалпы стили
    app.setStyle("Fusion")
    
    window = Lab01App()
    window.show()
    sys.exit(app.exec())