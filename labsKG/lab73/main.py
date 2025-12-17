import sys
import random
import math
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QGroupBox,
    QTextEdit, QSizePolicy, QScrollBar
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QRadialGradient, QLinearGradient
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF

# ==========================================
# КЛАСС: Жүк (Гиря же Белгисиз нерсе)
# ==========================================
class WeightItem:
    def __init__(self, mass, pos: QPointF, is_unknown=False):
        self.mass = mass
        self.pos = pos
        self.r = 15 + (mass / 10) # Массасына жараша радиусу чоңоёт
        if self.r > 30: self.r = 30
        
        self.is_unknown = is_unknown
        self.dragging = False
        self.on_plate = None  # 'left', 'right' же None

# ==========================================
# ВИЗУАЛИЗАЦИЯ: Тараза
# ==========================================
class ScalesWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(700, 450)
        self.setStyleSheet("background-color: #f4f4f4; border: 1px solid #aaa; border-radius: 8px;")
        
        # Таразанын параметрлери
        self.center = QPointF(350, 180)  # Төөнөгүчтүн орду
        self.beam_length = 400
        self.plate_radius = 50
        
        # Физика
        self.beam_angle = 0.0
        self.target_angle = 0.0
        
        # Жүктөр
        self.items = []
        self.dragged_item = None
        self.unknown_mass_val = 0
        
        # Анимация
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(20)
        
        self.create_experiment()

    def create_experiment(self):
        """Жаңы эксперимент түзүү"""
        self.items = []
        
        # 1. Стандарттуу гирлер (оң жакта тизилип турат)
        masses = [5, 10, 10, 20, 20, 50, 100]
        x0 = 600
        y0 = 350
        for i, m in enumerate(masses):
            # Гирлерди катар-катар тизүү
            row = i // 4
            col = i % 4
            pos = QPointF(x0 + col * 40, y0 - row * 40)
            self.items.append(WeightItem(m, pos, is_unknown=False))
            
        # 2. Белгисиз нерсе (сол жактагы табакка түшөт)
        self.unknown_mass_val = random.choice([25, 35, 45, 55, 65, 75, 85, 95, 115, 125])
        
        # Сол табактын координатасын табабыз
        left_plate_pos = self.get_plate_pos('left')
        unknown_item = WeightItem(self.unknown_mass_val, QPointF(left_plate_pos.x(), left_plate_pos.y() - 20), is_unknown=True)
        unknown_item.on_plate = 'left'
        self.items.append(unknown_item)
        
        # Таразаны нөлгө түшүрүү
        self.beam_angle = 0.0
        self.update()

    def get_plate_pos(self, side):
        """Табактын борборун эсептөө (бурчка жараша)"""
        angle = self.beam_angle
        if side == 'left':
            offset = -self.beam_length / 2
        else:
            offset = self.beam_length / 2
            
        # Айлануу формуласы
        rx = offset * math.cos(angle)
        ry = offset * math.sin(angle)
        
        # Табак илинген жиптин узундугу (80 пиксель)
        return QPointF(self.center.x() + rx, self.center.y() + ry + 100)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Негизи (Стойка)
        painter.setPen(QPen(Qt.black, 1))
        grad_base = QLinearGradient(self.center.x()-10, 0, self.center.x()+10, 0)
        grad_base.setColorAt(0, QColor(100, 100, 100))
        grad_base.setColorAt(0.5, QColor(200, 200, 200))
        grad_base.setColorAt(1, QColor(100, 100, 100))
        painter.setBrush(grad_base)
        painter.drawRect(int(self.center.x()) - 10, int(self.center.y()), 20, 200)
        
        # Төмөнкү платформа
        painter.drawRect(int(self.center.x()) - 60, int(self.center.y()) + 200, 120, 20)

        # 2. Рычаг (Балка)
        painter.save()
        painter.translate(self.center)
        painter.rotate(math.degrees(self.beam_angle))
        
        grad_beam = QLinearGradient(0, -10, 0, 10)
        grad_beam.setColorAt(0, QColor(180, 180, 180))
        grad_beam.setColorAt(1, QColor(120, 120, 120))
        painter.setBrush(grad_beam)
        painter.drawRoundedRect(int(-self.beam_length/2), -10, int(self.beam_length), 20, 5, 5)
        
        # Ортосундагы болт
        painter.setBrush(Qt.darkGray)
        painter.drawEllipse(-5, -5, 10, 10)
        painter.restore()

        # 3. Табактар жана жиптер
        self.draw_plate(painter, 'left')
        self.draw_plate(painter, 'right')

        # 4. Жүктөр
        for item in self.items:
            self.draw_item(painter, item)

    def draw_plate(self, painter, side):
        # Рычагдагы илмек чекити
        angle = self.beam_angle
        offset = -self.beam_length / 2 if side == 'left' else self.beam_length / 2
        
        hook_x = self.center.x() + offset * math.cos(angle)
        hook_y = self.center.y() + offset * math.sin(angle)
        hook_pt = QPointF(hook_x, hook_y)
        
        # Табактын борбору
        plate_center = self.get_plate_pos(side)
        
        # Жиптер (үч бурчтук формасында)
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        painter.drawLine(hook_pt, QPointF(plate_center.x() - 40, plate_center.y()))
        painter.drawLine(hook_pt, QPointF(plate_center.x() + 40, plate_center.y()))
        
        # Табактын өзү (жарым сфера)
        painter.setBrush(QColor(220, 220, 220))
        path = QPainterPath()
        path.moveTo(plate_center.x() - 50, plate_center.y())
        path.arcTo(plate_center.x() - 50, plate_center.y() - 15, 100, 40, 180, 180) # Төмөн ийилген
        path.closeSubpath()
        painter.drawPath(path)
        # Үстүңкү эллипс (ичи)
        painter.setBrush(QColor(200, 200, 200))
        painter.drawEllipse(plate_center.x() - 50, plate_center.y() - 10, 100, 20)

    def draw_item(self, painter, item):
        painter.save()
        painter.translate(item.pos)
        
        if item.is_unknown:
            # Белгисиз нерсе (Көк кутуча)
            painter.setBrush(QColor(70, 130, 180))
            painter.setPen(Qt.black)
            sz = item.r * 2
            painter.drawRect(int(-item.r), int(-item.r), int(sz), int(sz))
            painter.setPen(Qt.white)
            painter.drawText(int(-item.r), int(-item.r), int(sz), int(sz), Qt.AlignCenter, "?")
        else:
            # Гиря (Алтын түстө)
            grad = QRadialGradient(-5, -5, item.r*2)
            grad.setColorAt(0, QColor(255, 215, 0)) # Gold
            grad.setColorAt(1, QColor(184, 134, 11)) # Dark Gold
            painter.setBrush(grad)
            painter.setPen(QColor(100, 70, 0))
            painter.drawEllipse(QPointF(0, 0), item.r, item.r)
            
            # Массасын жазуу
            painter.setPen(Qt.black)
            font = QFont("Arial", 8, QFont.Bold)
            painter.setFont(font)
            painter.drawText(QRectF(-item.r, -item.r, item.r*2, item.r*2), Qt.AlignCenter, str(item.mass))
            
        painter.restore()

    def mousePressEvent(self, event):
        p = event.position()
        # Жүктөрдү тескери иретте карайбыз (үстүндөгүсүн алуу үчүн)
        for item in reversed(self.items):
            # Текшерүү: чычкан itemдин ичиндеби?
            dist = (item.pos - p).manhattanLength()
            limit = item.r + 5
            if dist <= limit:
                item.dragging = True
                self.dragged_item = item
                return

    def mouseMoveEvent(self, event):
        if self.dragged_item:
            p = event.position()
            # Чектөөлөр (экрандан чыгып кетпеши үчүн)
            x = max(20, min(self.width()-20, p.x()))
            y = max(20, min(self.height()-20, p.y()))
            self.dragged_item.pos = QPointF(x, y)
            self.dragged_item.on_plate = None # Сүйрөп жатканда табакта эмес
            self.update()

    def mouseReleaseEvent(self, event):
        if self.dragged_item:
            # Табактарга жакынбы?
            left_c = self.get_plate_pos('left')
            right_c = self.get_plate_pos('right')
            
            p = self.dragged_item.pos
            
            if (p - left_c).manhattanLength() < 60:
                self.dragged_item.on_plate = 'left'
            elif (p - right_c).manhattanLength() < 60:
                self.dragged_item.on_plate = 'right'
            else:
                self.dragged_item.on_plate = None
                
            self.dragged_item.dragging = False
            self.dragged_item = None
            self.update_physics()
            self.update()

    def update_physics(self):
        # Массаларды эсептөө
        m_left = sum(i.mass for i in self.items if i.on_plate == 'left')
        m_right = sum(i.mass for i in self.items if i.on_plate == 'right')
        
        diff = m_right - m_left
        # Максималдуу бурч (20 градус)
        max_angle = math.radians(20)
        
        # Айырмага жараша бурчту аныктоо (сезимталдык)
        self.target_angle = max(-max_angle, min(max_angle, diff / 50.0))

    def animate(self):
        # Бурчту максаттуу бурчка жакындатуу (инерция)
        diff = self.target_angle - self.beam_angle
        if abs(diff) > 0.001:
            self.beam_angle += diff * 0.1
            self.update()
            
            # Табактар кыймылдаганда жүктөр да кошо жылышы керек
            self.update_items_on_plates()

    def update_items_on_plates(self):
        left_c = self.get_plate_pos('left')
        right_c = self.get_plate_pos('right')
        
        # Жүктөрдү табактын үстүнө жайгаштыруу (үйүлүп калбашы үчүн жөнөкөй логика)
        l_items = [i for i in self.items if i.on_plate == 'left' and not i.dragging]
        r_items = [i for i in self.items if i.on_plate == 'right' and not i.dragging]
        
        for idx, item in enumerate(l_items):
            # Бири-биринин үстүнө тизүү
            item.pos = QPointF(left_c.x(), left_c.y() - 10 - idx * (item.r * 1.5))
            
        for idx, item in enumerate(r_items):
            item.pos = QPointF(right_c.x(), right_c.y() - 10 - idx * (item.r * 1.5))

    def get_unknown_mass(self):
        return self.unknown_mass_val

# ==========================================
# НЕГИЗГИ ТЕРЕЗЕ
# ==========================================
class Lab03App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш №3: Ийин таразасы, нерсенин массасын аныктоо")
        self.resize(1100, 600)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # --- СОЛ ЖАК: Визуализация ---
        left_group = QGroupBox("Тажрыйба стенди")
        left_layout = QVBoxLayout()
        self.scales = ScalesWidget()
        left_layout.addWidget(self.scales)
        left_group.setLayout(left_layout)
        main_layout.addWidget(left_group, stretch=3)

        # --- ОҢ ЖАК: Башкаруу ---
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, stretch=2)

        # 1. Тапшырма
        task_group = QGroupBox("Тапшырма")
        task_layout = QVBoxLayout()
        info = QLabel(
            "1. Сол жактагы табакта белгисиз нерсе (?) турат.\n"
            "2. Оң жактагы гирлерди колдонуп, таразаны теңдеңиз.\n"
            "3. Тең салмактуулук болгондо, гирлердин суммасын эсептеп, жазыңыз."
        )
        info.setWordWrap(True)
        task_layout.addWidget(info)
        task_group.setLayout(task_layout)
        right_panel.addWidget(task_group)

        # 2. Киргизүү
        input_group = QGroupBox("Жоопту киргизүү")
        input_layout = QVBoxLayout()
        
        self.inp_mass = QLineEdit()
        self.inp_mass.setPlaceholderText("Масса (грамм)")
        
        input_layout.addWidget(QLabel("Белгисиз нерсенин массасы:"))
        input_layout.addWidget(self.inp_mass)
        input_group.setLayout(input_layout)
        right_panel.addWidget(input_group)

        # 3. Башкаруу
        ctrl_group = QGroupBox("Башкаруу")
        ctrl_layout = QVBoxLayout()
        
        self.btn_check = QPushButton("Текшерүү")
        self.btn_check.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 35px;")
        self.btn_check.clicked.connect(self.check_answer)
        
        self.btn_new = QPushButton("Жаңы эксперимент")
        self.btn_new.clicked.connect(self.start_new)
        
        ctrl_layout.addWidget(self.btn_check)
        ctrl_layout.addWidget(self.btn_new)
        ctrl_group.setLayout(ctrl_layout)
        right_panel.addWidget(ctrl_group)

        # 4. Журнал
        res_group = QGroupBox("Журнал")
        res_layout = QVBoxLayout()
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        res_layout.addWidget(self.txt_log)
        res_group.setLayout(res_layout)
        right_panel.addWidget(res_group, stretch=1)

    def start_new(self):
        self.scales.create_experiment()
        self.inp_mass.clear()
        self.txt_log.append("--- Жаңы эксперимент башталды ---")

    def check_answer(self):
        text = self.inp_mass.text()
        if not text:
            QMessageBox.warning(self, "Ката", "Массаны жазыңыз!")
            return
            
        try:
            user_mass = float(text)
        except ValueError:
            QMessageBox.critical(self, "Ката", "Сандарды гана жазыңыз!")
            return

        real_mass = self.scales.get_unknown_mass()
        
        if user_mass == real_mass:
            self.txt_log.append(f"<span style='color:green'>✅ ТУУРА! Масса = {real_mass} г</span>")
        else:
            self.txt_log.append(f"<span style='color:red'>❌ КАТА. Сиздин жооп: {user_mass} г</span>")
            # Жардам: Тараза теңделдиби?
            diff = abs(self.scales.beam_angle)
            if diff > 0.05:
                self.txt_log.append("<i>Кеңеш: Тараза толук теңделе элек!</i>")

if __name__ == "__main__":
    from PySide6.QtGui import QPainterPath # Import added just in case
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = Lab03App()
    win.show()
    sys.exit(app.exec())