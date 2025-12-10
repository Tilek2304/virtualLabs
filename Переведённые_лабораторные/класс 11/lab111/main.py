# lab_pendulum_g.py
# Зарыйтуу: pip install PySide6
import sys, math, random, time
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSlider, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer, QPointF

class PendulumWidget(QFrame):
    """Анимированный маятник: длина l (px), угол theta, трение, визуализация."""
    def __init__(self, parent=None):
