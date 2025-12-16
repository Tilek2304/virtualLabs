import sys
import random
import math
from statistics import mean
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QSplitter
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath, QLinearGradient, QRadialGradient
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF

# ==========================================
# 1. МЕНЗУРКА ВИДЖЕТИ (Көлөмдү өлчөө)
# ==========================================
class MenzurkaWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 400)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")
        
        # Анимация
        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(30)
        
        self.state = 0 # 0=үстүндө, 1=түшүүдө, 2=астында, 3=көтөрүлүүдө
        self.anim_t = 0.0
        self.anim_speed = 0.03
        
        # Демейки маанилер (кийин set_params менен өзгөрөт)
        self.total_volume = 200
        self.V1 = 100
        self.V_body = 50
        self.divisions = 10

    def set_params(self, total_v, v1, v_body):
        self.total_volume = total_v
        self.V1 = v1
        self.V_body = v_body
        self.divisions = 20 # Туруктуу бөлүнүү
        self.state = 0
        self.anim_t = 0.0
        self.update()

    def on_timer(self):
        self.phase += 0.15
        if self.phase > 6.28: self.phase -= 6.28
        
        if self.state == 1:
            self.anim_t += self.anim_speed
            if self.anim_t >= 1.0:
                self.anim_t = 1.0
                self.state = 2
        elif self.state == 3:
            self.anim_t -= self.anim_speed
            if self.anim_t <= 0.0:
                self.anim_t = 0.0
                self.state = 0
        self.update()

    def toggle_immersion(self):
        if self.state == 0: self.state = 1
        elif self.state == 2: self.state = 3

    def get_current_volume(self):
        return self.V1 + self.V_body * self.anim_t

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        cyl_w = int(w * 0.5)
        cyl_h = int(h * 0.8)
        cyl_x = int((w - cyl_w) / 2)
        cyl_y = int(h * 0.1)

        # Айнек фон
        grad = QLinearGradient(cyl_x, 0, cyl_x+cyl_w, 0)
        grad.setColorAt(0, QColor(220, 230, 240, 100))
        grad.setColorAt(0.5, QColor(255, 255, 255, 150))
        grad.setColorAt(1, QColor(220, 230, 240, 100))
        painter.setBrush(grad)
        painter.setPen(QPen(Qt.gray, 2))
        painter.drawRect(cyl_x, cyl_y, cyl_w, cyl_h)

        # Суюктук
        inner_x = cyl_x + 4
        inner_w = cyl_w - 8
        inner_y = cyl_y + 4
        inner_h = cyl_h - 8
        
        cur_v = self.get_current_volume()
        level_h = inner_h * (cur_v / self.total_volume)
        liquid_top = inner_y + inner_h - level_h
        
        path = QPainterPath()
        path.moveTo(inner_x, inner_y + inner_h)
        path.lineTo(inner_x, liquid_top)
        for i in range(21):
            t = i / 20
            x = inner_x + t * inner_w
            y = liquid_top + math.sin(self.phase + t*10) * 2
            path.lineTo(x, y)
        path.lineTo(inner_x + inner_w, inner_y + inner_h)
        path.closeSubpath()
        
        painter.setBrush(QColor(0, 150, 255, 150))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

        # Шкала
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Arial", 8))
        for i in range(self.divisions + 1):
            val = int(i * (self.total_volume / self.divisions))
            y = inner_y + inner_h - (i / self.divisions) * inner_h
            painter.drawLine(inner_x, int(y), inner_x + 10, int(y))
            if i % 2 == 0:
                painter.drawText(inner_x + 15, int(y)+4, str(val))

        # Тело (шар)
        body_r = min(25, inner_w // 4)
        start_y = inner_y - 30
        end_y = liquid_top + body_r + 5
        cur_y = start_y + (end_y - start_y) * self.anim_t
        cur_x = inner_x + inner_w / 2
        
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(int(cur_x), int(cyl_y - 20), int(cur_x), int(cur_y))
        
        painter.setBrush(QColor(100, 100, 100)) # Металл түсү
        painter.drawEllipse(QPointF(cur_x, cur_y), body_r, body_r)

# ==========================================
# 2. ТАРАЗА ВИДЖЕТИ (Массаны өлчөө)
# ==========================================
class WeightItem:
    def __init__(self, mass, x, y, is_body=False):
        self.mass = mass
        self.pos = QPointF(x, y)
        self.r = 12 + mass / 20
        if self.r > 25: self.r = 25
        self.is_body = is_body
        self.dragging = False
        self.on_plate = None

class ScalesWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(350, 300)
        self.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ccc; border-radius: 8px;")
        
        self.center = QPointF(175, 100)
        self.beam_len = 240
        self.angle = 0.0
        self.target_angle = 0.0
        self.items = []
        self.dragged = None
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(20)
        
        self.init_weights()

    def init_weights(self):
        self.items = []
        # Гирлер (Тай туяктар)
        masses = [5, 10, 20, 20, 50, 100]
        start_x = 20
        start_y = 250
        for i, m in enumerate(masses):
            self.items.append(WeightItem(m, start_x + i * 35, start_y))
            
        # Белгисиз нерсе (башында сол табакта турат)
        self.unknown_body = WeightItem(50, 0, 0, is_body=True)
        self.unknown_body.on_plate = 'left'
        self.items.append(self.unknown_body)
        self.update_layout()

    def set_body_mass(self, mass):
        self.unknown_body.mass = mass
        # Таразаны баштапкы абалга келтирүү
        for item in self.items:
            if not item.is_body:
                item.on_plate = None
                item.pos.setY(250) # Астыга түшүрүү
        
        self.unknown_body.on_plate = 'left'
        self.angle = 0.0
        self.update_layout()

    def get_plate_pos(self, side):
        offset = -self.beam_len/2 if side == 'left' else self.beam_len/2
        rx = offset * math.cos(self.angle)
        ry = offset * math.sin(self.angle)
        return QPointF(self.center.x() + rx, self.center.y() + ry + 80)

    def update_layout(self):
        left_p = self.get_plate_pos('left')
        right_p = self.get_plate_pos('right')
        
        l_items = [i for i in self.items if i.on_plate == 'left' and not i.dragging]
        r_items = [i for i in self.items if i.on_plate == 'right' and not i.dragging]
        
        for k, item in enumerate(l_items):
            item.pos = QPointF(left_p.x(), left_p.y() - 10 - k*15)
        for k, item in enumerate(r_items):
            item.pos = QPointF(right_p.x(), right_p.y() - 10 - k*15)

    def animate(self):
        m_l = sum(i.mass for i in self.items if i.on_plate == 'left')
        m_r = sum(i.mass for i in self.items if i.on_plate == 'right')
        diff = m_r - m_l
        self.target_angle = max(-0.3, min(0.3, diff / 100))
        
        delta = self.target_angle - self.angle
        self.angle += delta * 0.1
        self.update_layout()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Негизи
        painter.setBrush(QColor(200, 200, 200))
        painter.drawRect(int(self.center.x())-5, int(self.center.y()), 10, 150)
        painter.drawRect(int(self.center.x())-40, int(self.center.y())+150, 80, 10)
        
        # Балка
        painter.save()
        painter.translate(self.center)
        painter.rotate(math.degrees(self.angle))
        painter.setBrush(QColor(150, 150, 180))
        painter.drawRect(int(-self.beam_len/2), -5, int(self.beam_len), 10)
        painter.restore()
        
        # Табактар
        self.draw_plate(painter, 'left')
        self.draw_plate(painter, 'right')
        
        # Жүктөр
        for item in self.items:
            painter.setPen(Qt.black)
            if item.is_body:
                painter.setBrush(QColor(100, 100, 100)) # Body
            else:
                painter.setBrush(QColor(255, 215, 0)) # Gold
            
            painter.drawEllipse(item.pos, item.r, item.r)
            if not item.is_body:
                painter.drawText(item.pos.x()-10, item.pos.y()+5, str(item.mass))

    def draw_plate(self, painter, side):
        pt = self.get_plate_pos(side)
        # Жиптер
        offset = -self.beam_len/2 if side == 'left' else self.beam_len/2
        top_x = self.center.x() + offset * math.cos(self.angle)
        top_y = self.center.y() + offset * math.sin(self.angle)
        painter.drawLine(int(top_x), int(top_y), int(pt.x()), int(pt.y()))
        # Табак
        painter.setBrush(QColor(230, 230, 230))
        painter.drawChord(int(pt.x()-30), int(pt.y()-10), 60, 40, 180*16, 180*16)

    def mousePressEvent(self, event):
        for item in reversed(self.items):
            if (item.pos - event.position()).manhattanLength() < item.r + 5:
                item.dragging = True
                self.dragged = item
                return
    
    def mouseMoveEvent(self, event):
        if self.dragged:
            self.dragged.pos = event.position()
            self.dragged.on_plate = None
    
    def mouseReleaseEvent(self, event):
        if self.dragged:
            l_p = self.get_plate_pos('left')
            r_p = self.get_plate_pos('right')
            p = self.dragged.pos
            
            if (p - l_p).manhattanLength() < 50: self.dragged.on_plate = 'left'
            elif (p - r_p).manhattanLength() < 50: self.dragged.on_plate = 'right'
            else: self.dragged.on_plate = None
            
            self.dragged.dragging = False
            self.dragged = None

    def get_measurements(self):
        m_l = sum(i.mass for i in self.items if i.on_plate == 'left')
        m_r = sum(i.mass for i in self.items if i.on_plate == 'right')
        return m_l, m_r

# ==========================================
# 3. НЕГИЗГИ ТЕРЕЗЕ
# ==========================================
class LabDensityApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораториялык иш №5: Катуу нерсенин тыгыздыгы")
        self.resize(1100, 700)
        
        # Материалдар (тыгыздыгы г/мл)
        self.materials = {
            " жыгач (дуб)": 0.7,
            "алюминий": 2.7,
            "темир": 7.8,
            "жез": 8.9,
            "коргошун": 11.3
        }
        self.current_material = ""
        self.true_mass = 0
        self.true_vol = 0
        
        self.setup_ui()
        self.new_experiment()

    def setup_ui(self):
        main = QHBoxLayout(self)
        
        # Сол жак (Аспаптар)
        left_area = QWidget()
        left_layout = QVBoxLayout(left_area)
        
        scale_group = QGroupBox("1. Массаны өлчөө (Тараза)")
        sl = QVBoxLayout()
        self.scales = ScalesWidget()
        sl.addWidget(self.scales)
        scale_group.setLayout(sl)
        
        menz_group = QGroupBox("2. Көлөмдү өлчөө (Мензурка)")
        ml = QVBoxLayout()
        self.menzurka = MenzurkaWidget()
        self.btn_immerse = QPushButton("Түшүрүү / Көтөрүү")
        self.btn_immerse.clicked.connect(self.menzurka.toggle_immersion)
        ml.addWidget(self.menzurka)
        ml.addWidget(self.btn_immerse)
        menz_group.setLayout(ml)
        
        left_layout.addWidget(scale_group, 1)
        left_layout.addWidget(menz_group, 1)
        main.addWidget(left_area, 1)

        # Оң жак (Башкаруу жана Таблица)
        right_area = QWidget()
        right_layout = QVBoxLayout(right_area)
        
        # Тапшырма
        task_g = QGroupBox("Тапшырма")
        task_l = QVBoxLayout()
        task_l.addWidget(QLabel("1. Тараза менен нерсенин массасын (m) табыңыз."))
        task_l.addWidget(QLabel("2. Мензурка менен нерсенин көлөмүн (V) табыңыз."))
        task_l.addWidget(QLabel("3. Тыгыздыкты эсептеңиз: ρ = m / V."))
        task_g.setLayout(task_l)
        right_layout.addWidget(task_g)
        
        # Киргизүү
        inp_g = QGroupBox("Маалыматтарды киргизүү")
        inp_l = QVBoxLayout()
        self.in_m = QLineEdit(); self.in_m.setPlaceholderText("Масса m (г)")
        self.in_v = QLineEdit(); self.in_v.setPlaceholderText("Көлөм V (мл)")
        self.in_rho = QLineEdit(); self.in_rho.setPlaceholderText("Тыгыздык ρ (г/мл)")
        
        inp_l.addWidget(QLabel("Масса (m):"))
        inp_l.addWidget(self.in_m)
        inp_l.addWidget(QLabel("Көлөм (V):"))
        inp_l.addWidget(self.in_v)
        inp_l.addWidget(QLabel("Тыгыздык (ρ):"))
        inp_l.addWidget(self.in_rho)
        inp_g.setLayout(inp_l)
        right_layout.addWidget(inp_g)
        
        # Баскычтар
        btn_check = QPushButton("Текшерүү жана Жазуу")
        btn_check.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_check.clicked.connect(self.check_and_add)
        
        btn_new = QPushButton("Жаңы эксперимент")
        btn_new.clicked.connect(self.new_experiment)
        
        right_layout.addWidget(btn_check)
        right_layout.addWidget(btn_new)
        
        # Таблица
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["m (г)", "V (мл)", "ρ (г/мл)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(QLabel("Өлчөө таблицасы:"))
        right_layout.addWidget(self.table)
        
        self.lbl_res = QLabel("")
        right_layout.addWidget(self.lbl_res)
        
        main.addWidget(right_area, 1)

    def new_experiment(self):
        # 1. Материалды жана тыгыздыкты тандайбыз
        name, rho = random.choice(list(self.materials.items()))
        self.current_material = name
        
        # 2. Чектөөлөрдү эсептейбиз
        # а) Масса боюнча чектөө: Гирлердин суммасы 205г, биз 200г ашпайбыз
        max_vol_by_mass = int(200 / rho)
        
        # б) Көлөм боюнча чектөө: Мензурка чоңураак болушу керек (мисалы 250мл)
        # Нерсе өтө чоң болбошу керек, айталы мензурканын 1/3 бөлүгүнөн ашпасын
        max_vol_by_size = 80 
        
        # Эки чектөөнүн кичинесин алабыз
        max_vol = min(max_vol_by_mass, max_vol_by_size)
        
        # Өтө кичине болуп калбашы үчүн (минималдуу 10 мл)
        if max_vol < 10: max_vol = 10
        
        # 3. Чыныгы маанилерди генерациялоо
        self.true_vol = random.randint(10, max_vol)
        self.true_mass = round(self.true_vol * rho, 1)
        
        # 4. Виджеттерди жаңылоо
        self.scales.set_body_mass(self.true_mass)
        
        # Мензурканы жөндөө
        v_total = 250 # Мензурканын көлөмүн 250 мл кылдык (кенен болуш үчүн)
        
        # V1 (суунун деңгээли) ташып кетпегидей болушу керек:
        # V1 + V_body <= V_total - запас (20мл)
        max_v1 = v_total - self.true_vol - 20
        min_v1 = 50 # Минималдуу суу
        
        if max_v1 < min_v1: max_v1 = min_v1 # Коопсуздук
        
        v1 = random.randint(min_v1, max_v1)
        self.menzurka.set_params(v_total, v1, self.true_vol)
        
        # Талааларды тазалоо
        self.in_m.clear()
        self.in_v.clear()
        self.in_rho.clear()
        self.lbl_res.setText("--- Жаңы тапшырма берилди ---")

    def check_and_add(self):
        try:
            u_m = float(self.in_m.text())
            u_v = float(self.in_v.text())
            u_rho = float(self.in_rho.text())
        except:
            QMessageBox.warning(self, "Ката", "Сандарды туура киргизиңиз!")
            return
            
        # Текшерүү
        ok_m = abs(u_m - self.true_mass) <= 5 # 1г каталыкка жол берилет
        ok_v = abs(u_v - self.true_vol) <= 10 # 2мл каталык
        
        true_rho = self.true_mass / self.true_vol
        ok_rho = abs(u_rho - true_rho) <= 1
        
        if ok_m and ok_v and ok_rho:
            self.lbl_res.setText(f"<span style='color:green'><b>ТУУРА! Бул: {self.current_material.upper()}</b></span>")
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(u_m)))
            self.table.setItem(row, 1, QTableWidgetItem(str(u_v)))
            self.table.setItem(row, 2, QTableWidgetItem(str(u_rho)))
        else:
            msg = "КАТАЛАР БАР:\n"
            if not ok_m: msg += f"- Масса туура эмес (Чыныгы: {self.true_mass})\n"
            if not ok_v: msg += f"- Көлөм туура эмес (Чыныгы: {self.true_vol})\n"
            if not ok_rho: msg += f"- Тыгыздык туура эмес"
            QMessageBox.warning(self, "Ката", msg)
            
            print(true_rho, self.true_mass, self.true_vol)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = LabDensityApp()
    win.show()
    sys.exit(app.exec())