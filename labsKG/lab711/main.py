# lab_center_of_mass.py
# Требуется: pip install PySide6, numpy, pandas
import sys, time, json, random, math
from dataclasses import dataclass, asdict
from typing import List, Tuple
import numpy as np, pandas as pd

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QFrame,
    QFileDialog, QDoubleSpinBox, QCheckBox, QMessageBox
)
from PySide6.QtGui import QPainter, QColor, QFont, QPen
from PySide6.QtCore import Qt, QPointF

@dataclass
class Measurement:
    timestamp: float
    shape: str
    width: float
    height: float
    cx: float
    cy: float
    user_x: float
    user_y: float
    result: str

@dataclass
class SessionHeader:
    session_id: str
    user_id: str
    lab_id: str = "PHY-07-CENTER-MASS"
    version: str = "2.3"
    started_at: float = time.time()

@dataclass
class AnalysisSummary:
    count: int = 0

# --- Виджет фигуры ---
class ShapeWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(500, 300)
        self.shape = "Тик бурчтук"
        self.width_val = 200
        self.height_val = 100
        self.cx = self.width_val / 2
        self.cy = self.height_val / 2
        self.hangs: List[Tuple[float, float, float]] = []
        self.found_point: Tuple[float, float] = None

    def set_shape(self, shape, w, h):
        self.shape = shape
        self.width_val = w
        self.height_val = h
        if shape == "Тик бурчтук":
            self.cx, self.cy = w / 2, h / 2
        elif shape == "Үч бурчтук":
            self.cx, self.cy = w / 2, h * 2 / 3
        elif shape == "Г-түрүндөгү":
            self.cx, self.cy = w * 0.4, h * 0.6
        self.hangs.clear()
        self.found_point = None
        self.update()

    def clear_hangs(self):
        self.hangs.clear()
        self.found_point = None
        self.update()

    def mousePressEvent(self, event):
        ox, oy = 50, 50
        x_click = float(event.position().x() - ox)
        y_click = float(event.position().y() - oy)
        if 0 <= x_click <= self.width_val and 0 <= y_click <= self.height_val:
            angle_deg = random.uniform(-25, 25)
            angle_rad = math.radians(angle_deg)
            self.hangs.append((x_click, y_click, angle_rad))
            self.compute_found_center()
            self.update()

    def compute_found_center(self):
        if len(self.hangs) < 2:
            self.found_point = None
            return
        lines = []
        for (x_rel, y_rel, ang) in self.hangs:
            d = np.array([math.sin(ang), math.cos(ang)], dtype=float)
            p0 = np.array([x_rel, y_rel], dtype=float)
            lines.append((p0, d))
        found = None
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                p0a, da = lines[i]
                p0b, db = lines[j]
                if abs(np.cross(da, db)) < 1e-3:
                    continue
                A = np.column_stack((da, -db))
                b = (p0b - p0a)
                try:
                    t = np.linalg.solve(A, b)
                    p = p0a + t[0] * da
                    found = (float(p[0]), float(p[1]))
                    break
                except np.linalg.LinAlgError:
                    continue
            if found is not None:
                break
        self.found_point = found

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(240, 240, 240))
        p.setBrush(QColor(180, 200, 250))
        p.setFont(QFont("Sans", 9))

        ox, oy = 50, 50
        w, h = self.width_val, self.height_val

        if self.shape == "Тик бурчтук":
            p.drawRect(ox, oy, w, h)
        elif self.shape == "Үч бурчтук":
            points = [
                QPointF(ox, oy + h),
                QPointF(ox + w, oy + h),
                QPointF(ox + w / 2, oy)
            ]
            p.drawPolygon(points)
        elif self.shape == "Г-түрүндөгү":
            p.drawRect(ox, oy, w // 2, h)
            p.drawRect(ox + w // 2, oy + h // 2, w // 2, h // 2)

        p.setBrush(QColor(220, 50, 50))
        
        pen = QPen(QColor(60, 60, 60))
        pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        for (x_rel, y_rel, ang) in self.hangs:
            d = np.array([math.sin(ang), math.cos(ang)], dtype=float)
            L = 600
            p1 = QPointF(ox + x_rel - d[0] * L, oy + y_rel - d[1] * L)
            p2 = QPointF(ox + x_rel + d[0] * L, oy + y_rel + d[1] * L)
            p.drawLine(p1, p2)

        if self.found_point is not None:
            fx, fy = self.found_point
            p.setBrush(QColor(0, 180, 0))
            p.setPen(Qt.SolidLine)
            p.drawEllipse(int(ox + fx) - 5, int(oy + fy) - 5, 10, 10)
            p.drawText(int(ox + fx) + 8, int(oy + fy) - 8, f"({fx:.1f},{fy:.1f})")

# --- Главное приложение ---
class CenterMassLab(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Определение центра тяжести -> Оордук борборун аныктоо
        self.setWindowTitle("Лабораториялык иш: Оордук борборун аныктоо (илүү ыкмасы)")
        self.resize(1100, 700)

        self.header = SessionHeader(session_id=str(int(time.time() * 1000)), user_id="student_local")
        self.measurements: List[Measurement] = []
        self.analysis = AnalysisSummary()

        root = QHBoxLayout(self)

        left_frame = QFrame(); left_layout = QVBoxLayout(left_frame); left_frame.setFixedWidth(400)
        left_layout.addWidget(QLabel("<b>Оордук борборун аныктоо</b>"))

        # КОТОРМО: Вопрос...
        question = QLabel("Чыныгы тажрыйбада оордук борборун кантип табышат?")
        question.setWordWrap(True)
        left_layout.addWidget(question)

        # КОТОРМО: Фигура
        left_layout.addWidget(QLabel("Фигура"))
        self.shape_select = QComboBox()
        self.shapes = ["Тик бурчтук", "Үч бурчтук", "Г-түрүндөгү"]
        for s in self.shapes: self.shape_select.addItem(s)
        left_layout.addWidget(self.shape_select)

        # КОТОРМО: Ширина, Высота
        left_layout.addWidget(QLabel("Туурасы (px)"))
        self.width_input = QDoubleSpinBox(); self.width_input.setRange(50, 300); self.width_input.setValue(200)
        left_layout.addWidget(self.width_input)
        left_layout.addWidget(QLabel("Бийиктиги (px)"))
        self.height_input = QDoubleSpinBox(); self.height_input.setRange(50, 300); self.height_input.setValue(120)
        left_layout.addWidget(self.height_input)

        # КОТОРМО: Ваши ответы -> Сиздин жооптор
        left_layout.addWidget(QLabel("<b>Сиздин жооптор</b>"))
        self.input_x = QLineEdit(); self.input_x.setPlaceholderText("Оордук борбору X (px)")
        self.input_y = QLineEdit(); self.input_y.setPlaceholderText("Оордук борбору Y (px)")
        left_layout.addWidget(self.input_x); left_layout.addWidget(self.input_y)

        # КОТОРМО: Найденный ЦТ -> Табылган ОБ
        self.found_label = QLabel("Табылган ОБ: —")
        left_layout.addWidget(self.found_label)
        
        # Кнопки
        # КОТОРМО: Применить -> Колдонуу
        self.btn_apply = QPushButton("Фигураны колдонуу"); self.btn_apply.clicked.connect(self.apply_shape)
        # КОТОРМО: Случайный -> Кокустан тандалган
        self.btn_random = QPushButton("Кокустан тандалган тажрыйба"); self.btn_random.clicked.connect(self.random_experiment)
        # КОТОРМО: Проверить -> Текшерүү
        self.btn_check = QPushButton("Жоопту текшерүү"); self.btn_check.clicked.connect(self.check_answer)
        # КОТОРМО: Показать ответ -> Жоопту көрсөтүү
        self.btn_show = QPushButton("Жоопту көрсөтүү"); self.btn_show.clicked.connect(self.show_answer)
        # КОТОРМО: Сброс -> Кайра баштоо
        self.btn_reset = QPushButton("Кайра баштоо"); self.btn_reset.clicked.connect(self.clear_measurements)
        # КОТОРМО: Очистить подвесы -> Илгичтерди тазалоо
        self.btn_clear_hangs = QPushButton("Илгичтерди тазалоо"); self.btn_clear_hangs.clicked.connect(self.clear_hangs)
        
        left_layout.addWidget(self.btn_apply); left_layout.addWidget(self.btn_random)
        left_layout.addWidget(self.btn_check); left_layout.addWidget(self.btn_show)
        left_layout.addWidget(self.btn_reset); left_layout.addWidget(self.btn_clear_hangs)

        # Экспорт
        exp = QHBoxLayout()
        self.csv_btn = QPushButton("Экспорт CSV"); self.csv_btn.clicked.connect(self.export_csv)
        self.json_btn = QPushButton("Сактоо JSON"); self.json_btn.clicked.connect(self.save_session_json)
        exp.addWidget(self.csv_btn); exp.addWidget(self.json_btn)
        left_layout.addLayout(exp)

        # Правая панель
        right_frame = QFrame(); right_layout = QVBoxLayout(right_frame)
        self.shape_widget = ShapeWidget()
        right_layout.addWidget(self.shape_widget)

        self.table = QTableWidget(0, 8)
        # КОТОРМО: Заголовки таблицы
        self.table.setHorizontalHeaderLabels(["t", "Фигура", "W", "H", "ОБ X", "ОБ Y", "Жооп X,Y", "Жыйынтык"])
        right_layout.addWidget(self.table)

        root.addWidget(left_frame); root.addWidget(right_frame)

        self.apply_shape()

    def apply_shape(self):
        shape = self.shape_select.currentText()
        w = float(self.width_input.value())
        h = float(self.height_input.value())
        self.shape_widget.set_shape(shape, w, h)
        self.found_label.setText("Табылган ОБ: —")

    def random_experiment(self):
        shape = random.choice(self.shapes)
        w = random.randint(80, 250)
        h = random.randint(80, 250)
        self.shape_select.setCurrentText(shape)
        self.width_input.setValue(w)
        self.height_input.setValue(h)
        self.shape_widget.set_shape(shape, w, h)
        self.input_x.clear(); self.input_y.clear()
        self.found_label.setText("Табылган ОБ: —")

    def check_answer(self):
        try:
            ux = float(self.input_x.text())
            uy = float(self.input_y.text())
        except Exception:
            QMessageBox.warning(self, "Ката", "X жана Y үчүн сан маанилерин киргизиңиз.")
            return
        cx, cy = self.shape_widget.cx, self.shape_widget.cy
        tol_x = max(2.0, 0.09 * max(1.0, abs(cx)))
        tol_y = max(2.0, 0.09 * max(1.0, abs(cy)))
        ok = abs(ux - cx) <= tol_x and abs(uy - cy) <= tol_y

        if self.shape_widget.found_point is not None:
            fx, fy = self.shape_widget.found_point
            self.found_label.setText(f"Табылган ОБ: ({fx:.1f}, {fy:.1f})")
        else:
            self.found_label.setText("Табылган ОБ: —")

        # КОТОРМО: Верно/Ошибка
        result = "Туура" if ok else f"Ката (ОБ=({cx:.1f},{cy:.1f}), piela ±{tol_x:.1f}, ±{tol_y:.1f})"
        QMessageBox.information(self, "Жыйынтык", result)

        meas = Measurement(
            timestamp=time.time(), shape=self.shape_select.currentText(),
            width=self.width_input.value(), height=self.height_input.value(),
            cx=cx, cy=cy, user_x=ux, user_y=uy, result=result
        )
        self.measurements.append(meas)
        self.append_table_row(meas)

    def show_answer(self):
        self.input_x.setText(f"{self.shape_widget.cx:.1f}")
        self.input_y.setText(f"{self.shape_widget.cy:.1f}")

    def clear_hangs(self):
        self.shape_widget.clear_hangs()
        self.found_label.setText("Табылган ОБ: —")

    def append_table_row(self, m: Measurement):
        row = self.table.rowCount(); self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(time.strftime("%H:%M:%S", time.localtime(m.timestamp))))
        self.table.setItem(row, 1, QTableWidgetItem(m.shape))
        self.table.setItem(row, 2, QTableWidgetItem(f"{m.width:.1f}"))
        self.table.setItem(row, 3, QTableWidgetItem(f"{m.height:.1f}"))
        self.table.setItem(row, 4, QTableWidgetItem(f"{m.cx:.1f}"))
        self.table.setItem(row, 5, QTableWidgetItem(f"{m.cy:.1f}"))
        self.table.setItem(row, 6, QTableWidgetItem(f"{m.user_x:.1f}, {m.user_y:.1f}"))
        self.table.setItem(row, 7, QTableWidgetItem(m.result))

    def clear_measurements(self):
        self.measurements.clear()
        self.table.setRowCount(0)
        self.input_x.clear(); self.input_y.clear()
        self.shape_widget.clear_hangs()
        self.found_label.setText("Табылган ОБ: —")

    def export_csv(self):
        if not self.measurements:
            QMessageBox.information(self, "Экспорт CSV", "Экспорттоо үчүн маалымат жок.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "CSV сактоо", "center_mass_session.csv", "CSV Files (*.csv)")
        if not path: return
        pd.DataFrame([asdict(m) for m in self.measurements]).to_csv(path, index=False)
        QMessageBox.information(self, "Экспорт CSV", "CSV сакталды.")

    def save_session_json(self):
        session = {
            "header": asdict(self.header),
            "measurements": [asdict(m) for m in self.measurements],
            "analysis": asdict(self.analysis),
            "metadata": {"units": {"W": "px", "H": "px", "X": "px", "Y": "px"}}
        }
        path, _ = QFileDialog.getSaveFileName(self, "JSON сактоо", "center_mass_session.json", "JSON Files (*.json)")
        if not path: return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, "JSON сактоо", "Сессия сакталды.")

# --- точка входа ---
def main():
    app = QApplication(sys.argv)
    win = CenterMassLab()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()