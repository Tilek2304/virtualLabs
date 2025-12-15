# lab_friction_visual.py
# Требуется: pip install PySide6, numpy, pandas
import sys, time, json, random
from dataclasses import dataclass, asdict
from typing import List
import numpy as np, pandas as pd

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QFrame,
    QFileDialog, QDoubleSpinBox, QCheckBox, QMessageBox
)
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt, QTimer

g = 9.81

@dataclass
class Measurement:
    timestamp: float
    mass_kg: float
    mu: float
    normal_N: float
    friction_N: float
    note: str = ""

@dataclass
class SessionHeader:
    session_id: str
    user_id: str
    lab_id: str = "PHY-07-FRICTION"
    version: str = "2.0"
    started_at: float = time.time()

@dataclass
class AnalysisSummary:
    mean_friction: float = 0.0
    std_friction: float = 0.0
    count: int = 0

# --- Виджет тела ---
class BodyWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(500, 250)
        self.mass = 10
        self.mu = 0.3
        self.x = 20
        self.speed = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(40)

    def set_params(self, m=None, mu=None):
        if m is not None: self.mass = m
        if mu is not None: self.mu = mu
        self.x = 20
        self.speed = 20.0
        self.update()

    def _tick(self):
        Ftr = self.mu * self.mass * g
        self.speed -= Ftr/500.0
        if self.speed < 0: self.speed = 0
        self.x += self.speed*0.5
        if self.x > self.width()-100: self.x = self.width()-100
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(240,240,240))
        ground_y = self.height()-40
        p.fillRect(0, ground_y, self.width(), 10, QColor(120,120,120))
        w,h = 80,40
        p.setBrush(QColor(100,150,200))
        p.drawRect(int(self.x), ground_y-h, w,h)
        p.setFont(QFont("Sans",9))
        p.drawText(int(self.x), ground_y-h-5, f"m={self.mass} кг, μ={self.mu}")

# --- Главное приложение ---
class FrictionLab(QWidget):
    def __init__(self):
        super().__init__()
        # КОТОРМО: Лаборатория: Сила трения -> Лабораториялык иш: Сүрүлүү күчү (Fсүр = μ·N)
        self.setWindowTitle("Лабораториялык иш: Сүрүлүү күчү (Fсүр = μ·N)")
        self.resize(1100, 700)

        self.header = SessionHeader(session_id=str(int(time.time()*1000)), user_id="student_local")
        self.measurements: List[Measurement] = []
        self.analysis = AnalysisSummary()

        root = QHBoxLayout(self)

        # Левая панель
        left_frame = QFrame(); left_layout = QVBoxLayout(left_frame); left_frame.setFixedWidth(380)
        left_layout.addWidget(QLabel("<b>Сүрүлүү күчү (Fсүр = μ·N)</b>"))

        # Масса
        # КОТОРМО: Масса (кг) -> Масса (кг)
        left_layout.addWidget(QLabel("Масса (кг)"))
        self.mass_input = QDoubleSpinBox(); self.mass_input.setRange(0.1, 100.0); self.mass_input.setValue(10.0)
        left_layout.addWidget(self.mass_input)

        # Кнопка применить изменения в массе
        # КОТОРМО: Применить... -> Массаны өзгөртүүнү колдонуу
        self.btn_apply_mass = QPushButton("Массаны өзгөртүүнү колдонуу")
        self.btn_apply_mass.clicked.connect(self.apply_mass_change)
        left_layout.addWidget(self.btn_apply_mass)

        # Материал
        # КОТОРМО: Материал (коэф...) -> Материал (сүрүлүү коэф. μ)
        left_layout.addWidget(QLabel("Материал (сүрүлүү коэф. μ)"))
        self.mu_select = QComboBox()
        # КОТОРМО: Материалдар (жыгач, темир, резина, муз)
        self.mu_values = {"Жыгач":0.4, "Темир":0.2, "Резина":0.8, "Муз":0.05}
        for k in self.mu_values: self.mu_select.addItem(k)
        left_layout.addWidget(self.mu_select)

        # Поля ответа ученика
        # КОТОРМО: Ваши ответы -> Сиздин жооптор
        left_layout.addWidget(QLabel("<b>Сиздин жооптор</b>"))
        self.input_Ftr = QLineEdit(); self.input_Ftr.setPlaceholderText("Fсүр (Н)")
        self.input_P = QLineEdit(); self.input_P.setPlaceholderText("P (Па)")
        left_layout.addWidget(self.input_Ftr); left_layout.addWidget(self.input_P)

        # Кнопки
        # КОТОРМО: Случайный -> Кокустан тандалган
        self.btn_random = QPushButton("Кокустан тандалган тажрыйба"); self.btn_random.clicked.connect(self.random_experiment)
        # КОТОРМО: Проверить -> Текшерүү
        self.btn_check = QPushButton("Жоопторду текшерүү"); self.btn_check.clicked.connect(self.check_answers)
        # КОТОРМО: Показать ответ -> Жоопту көрсөтүү
        self.btn_show = QPushButton("Жоопту көрсөтүү"); self.btn_show.clicked.connect(self.show_answer)
        # КОТОРМО: Сброс -> Кайра баштоо
        self.btn_reset = QPushButton("Кайра баштоо"); self.btn_reset.clicked.connect(self.clear_measurements)
        
        left_layout.addWidget(self.btn_random); left_layout.addWidget(self.btn_check)
        left_layout.addWidget(self.btn_show); left_layout.addWidget(self.btn_reset)

        # Экспорт
        exp = QHBoxLayout()
        self.csv_btn = QPushButton("Экспорт CSV"); self.csv_btn.clicked.connect(self.export_csv)
        self.json_btn = QPushButton("Сактоо JSON"); self.json_btn.clicked.connect(self.save_session_json)
        exp.addWidget(self.csv_btn); exp.addWidget(self.json_btn)
        left_layout.addLayout(exp)

        # Анализ
        # КОТОРМО: Автоанализ -> Автоанализ
        self.auto_recalc = QCheckBox("Автоанализ"); self.auto_recalc.setChecked(True)
        left_layout.addWidget(self.auto_recalc)
        # КОТОРМО: Среднее... -> Орточо Fсүр: —, σ: —, чекиттер: 0
        self.summary_label = QLabel("Орточо Fсүр: —, σ: —, чекиттер: 0")
        left_layout.addWidget(self.summary_label)

        # Правая панель
        right_frame = QFrame(); right_layout = QVBoxLayout(right_frame)
        self.body = BodyWidget()
        right_layout.addWidget(self.body)

        self.table = QTableWidget(0,5)
        # КОТОРМО: Заголовки таблицы
        self.table.setHorizontalHeaderLabels(["t","m (кг)","μ","N (Н)","Fсүр (Н)"])
        right_layout.addWidget(self.table)

        root.addWidget(left_frame); root.addWidget(right_frame)

    def apply_mass_change(self):
        m = float(self.mass_input.value())
        mu = self.mu_values[self.mu_select.currentText()]
        self.body.set_params(m=m, mu=mu)
        QMessageBox.information(self,"Маалымат",f"Масса {m} кг деп өзгөртүлдү")

    def add_point(self):
        m = float(self.mass_input.value())
        mu = self.mu_values[self.mu_select.currentText()]
        N = m*g
        Ftr = mu*N
        meas = Measurement(timestamp=time.time(), mass_kg=m, mu=mu, normal_N=N, friction_N=Ftr, note="")
        self.measurements.append(meas)
        self.body.set_params(m=m, mu=mu)
        self.append_table_row(meas)
        if self.auto_recalc.isChecked(): self.recalc_analysis()

    def append_table_row(self,m:Measurement):
        row = self.table.rowCount(); self.table.insertRow(row)
        self.table.setItem(row,0,QTableWidgetItem(time.strftime("%H:%M:%S",time.localtime(m.timestamp))))
        self.table.setItem(row,1,QTableWidgetItem(f"{m.mass_kg:.2f}"))
        self.table.setItem(row,2,QTableWidgetItem(f"{m.mu:.2f}"))
        self.table.setItem(row,3,QTableWidgetItem(f"{m.normal_N:.2f}"))
        self.table.setItem(row,4,QTableWidgetItem(f"{m.friction_N:.2f}"))

    def clear_measurements(self):
        self.measurements.clear(); self.table.setRowCount(0)
        self.summary_label.setText("Орточо Fсүр: —, σ: —, чекиттер: 0")
        self.input_Ftr.clear(); self.input_P.clear()

    def recalc_analysis(self):
        if not self.measurements: return
        vals = np.array([m.friction_N for m in self.measurements])
        mean, std = float(np.mean(vals)), float(np.std(vals,ddof=1)) if len(vals)>1 else 0.0
        self.analysis = AnalysisSummary(mean_friction=mean,std_friction=std,count=len(vals))
        self.summary_label.setText(f"Орточо Fсүр: {mean:.2f} Н, σ: {std:.2f}, чекиттер: {len(vals)}")

    def random_experiment(self):
        m = random.randint(5,30)
        mu = random.choice(list(self.mu_values.values()))
        self.mass_input.setValue(m)
        idx = list(self.mu_values.values()).index(mu)
        self.mu_select.setCurrentIndex(idx)
        self.body.set_params(m=m, mu=mu)
        self.input_Ftr.clear(); self.input_P.clear()

    def check_answers(self):
        try:
            F_user = float(self.input_Ftr.text())
            P_user = float(self.input_P.text())
        except:
            QMessageBox.warning(self,"Ката","Сан маанилерин киргизиңиз.")
            return
        m = float(self.mass_input.value())
        mu = self.mu_values[self.mu_select.currentText()]
        N = m*g
        F_true = mu*N
        P_true = N/0.01  # шарттуу аянт 0.01 м²
        ok_F = abs(F_user - F_true) <= 0.05*F_true
        ok_P = abs(P_user - P_true) <= 0.05*P_true
        
        result = "✅ Баары туура" if ok_F and ok_P else f"❌ Ката (Fсүр={F_true:.1f} Н, P={P_true:.1f} Па)"
        QMessageBox.information(self,"Жыйынтык",result)
        
        # таблицага жазуу
        row = self.table.rowCount(); self.table.insertRow(row)
        self.table.setItem(row,0,QTableWidgetItem(time.strftime("%H:%M:%S",time.localtime(time.time()))))
        self.table.setItem(row,1,QTableWidgetItem(str(m)))
        self.table.setItem(row,2,QTableWidgetItem(str(mu)))
        self.table.setItem(row,3,QTableWidgetItem(f"{N:.1f}"))
        self.table.setItem(row,4,QTableWidgetItem(f"{F_true:.1f}"))

    def show_answer(self):
        m = float(self.mass_input.value())
        mu = self.mu_values[self.mu_select.currentText()]
        N = m*g
        F_true = mu*N
        P_true = N/0.01
        self.input_Ftr.setText(f"{F_true:.1f}")
        self.input_P.setText(f"{P_true:.1f}")

    def export_csv(self):
        if not self.measurements: return
        path,_=QFileDialog.getSaveFileName(self,"CSV сактоо","friction_session.csv","CSV Files (*.csv)")
        if not path: return
        pd.DataFrame([asdict(m) for m in self.measurements]).to_csv(path,index=False)

    def save_session_json(self):
        session={"header":asdict(self.header),"measurements":[asdict(m) for m in self.measurements],
                 "analysis":asdict(self.analysis),"metadata":{"units":{"m":"kg","N":"N","Ftr":"N"}}}
        path,_=QFileDialog.getSaveFileName(self,"JSON сактоо","friction_session.json","JSON Files (*.json)")
        if not path: return
        with open(path,"w",encoding="utf-8") as f:
            json.dump(session,f,ensure_ascii=False,indent=2)

# --- точка входа ---
def main():
    app = QApplication(sys.argv)
    win = FrictionLab()
    win.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()