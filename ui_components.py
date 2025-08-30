# =============================================================================
#           HyperNesting v2.2 - ui_components.py (Corrected)
# =============================================================================
import sys
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QVBoxLayout, QPushButton, QLabel, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QDialog, QDialogButtonBox, QGraphicsView, QGraphicsScene,
                             QComboBox, QCheckBox, QGridLayout, QTextEdit,
                             QLineEdit, QFormLayout, QDoubleSpinBox, QRadioButton,
                             QSpinBox, QToolBar, QScrollArea, QSplitter, QGraphicsEllipseItem)
from PyQt6.QtGui import QBrush, QColor, QPen, QFont, QPolygonF
from PyQt6.QtCore import Qt, QSize, QPointF
import qtawesome as qta
import random

# --- 1.1: Auto Joint Dialog ---
class AutoJointDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent);self.setWindowTitle("Auto Joint");self.setMinimumWidth(500);main_layout = QVBoxLayout(self)
        description_label = QLabel("This function is used to prevent the pattern from falling in the cutting process.\nThe micro connect place will not be cut.")
        main_layout.addWidget(description_label);grid_layout = QGridLayout();style_group = QGroupBox("Style");style_layout = QVBoxLayout()
        self.by_count_radio = QRadioButton("Joint By Count");self.by_distance_radio = QRadioButton("Joint By Distance");self.by_count_radio.setChecked(True)
        style_layout.addWidget(self.by_count_radio);style_layout.addWidget(self.by_distance_radio);style_group.setLayout(style_layout);grid_layout.addWidget(style_group, 0, 0)
        special_group = QGroupBox("Special");special_layout = QVBoxLayout();self.no_joint_start_check = QCheckBox("No Joint at Start");self.corner_not_mic_check = QCheckBox("Corner is not mic")
        self.no_joint_start_check.setChecked(True);self.corner_not_mic_check.setChecked(True);special_layout.addWidget(self.no_joint_start_check);special_layout.addWidget(self.corner_not_mic_check)
        special_group.setLayout(special_layout);grid_layout.addWidget(special_group, 1, 0);settings_layout = QFormLayout();self.count_spin = QSpinBox();self.count_spin.setValue(4)
        self.length_combo = QComboBox();self.length_combo.addItems(["0.4mm", "0.5mm", "1.0mm", "2.0mm"]);self.apply_to_combo = QComboBox()
        self.apply_to_combo.addItems(["Apply to All Graphics", "Apply to Selected Graphics"]);settings_layout.addRow("Count:", self.count_spin);settings_layout.addRow("Length:", self.length_combo)
        settings_layout.addRow(self.apply_to_combo);grid_layout.addLayout(settings_layout, 0, 1);size_filter_group = QGroupBox("Size filter");size_filter_layout = QFormLayout()
        self.min_size_check = QCheckBox("Min-size:");self.max_size_check = QCheckBox("Max-size:");self.min_size_combo = QComboBox();self.min_size_combo.addItems(["10mm", "20mm", "50mm"])
        self.max_size_combo = QComboBox();self.max_size_combo.addItems(["100mm", "200mm", "500mm"]);size_filter_layout.addRow(self.min_size_check, self.min_size_combo)
        size_filter_layout.addRow(self.max_size_check, self.max_size_combo);size_filter_group.setLayout(size_filter_layout);grid_layout.addWidget(size_filter_group, 1, 1, Qt.AlignmentFlag.AlignTop)
        main_layout.addLayout(grid_layout);button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept);button_box.rejected.connect(self.reject);main_layout.addWidget(button_box)
    def get_settings(self):
        return {'style': 'By Count' if self.by_count_radio.isChecked() else 'By Distance','no_joint_at_start': self.no_joint_start_check.isChecked(),'corner_is_not_mic': self.corner_not_mic_check.isChecked(),'count': self.count_spin.value(),'length': self.length_combo.currentText(),'apply_to': self.apply_to_combo.currentText(),'use_min_filter': self.min_size_check.isChecked(),'min_size': self.min_size_combo.currentText() if self.min_size_check.isChecked() else None,'use_max_filter': self.max_size_check.isChecked(),'max_size': self.max_size_combo.currentText() if self.max_size_check.isChecked() else None}

# --- 1.2: Add Sheets Dialog ---
class AddSheetsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Sheets")
        self.setMinimumWidth(400)
        # --- THIS LINE IS NOW CORRECTED ---
        self.new_sheets_data = []
        # ----------------------------------
        main_layout = QVBoxLayout(self)
        standard_group = QGroupBox("Choose Standard Sheet Sizes");standard_layout = QVBoxLayout();self.standard_sheets_checkboxes = []
        standard_sizes = ["2500x1250", "3000x1500", "1000x2000"];self.all_sheets_checkbox = QCheckBox("All Sheets");standard_layout.addWidget(self.all_sheets_checkbox)
        for size in standard_sizes: checkbox = QCheckBox(size);self.standard_sheets_checkboxes.append(checkbox);standard_layout.addWidget(checkbox)
        standard_group.setLayout(standard_layout);main_layout.addWidget(standard_group);self.all_sheets_checkbox.stateChanged.connect(self.toggle_all_sheets)
        custom_group = QGroupBox("Add a Custom Sheet Size");custom_layout = QFormLayout();self.length_input = QLineEdit();self.width_input = QLineEdit();self.quantity_input = QLineEdit("1")
        custom_layout.addRow("Length (mm):", self.length_input);custom_layout.addRow("Width (mm):", self.width_input);custom_layout.addRow("Quantity:", self.quantity_input)
        custom_group.setLayout(custom_layout);main_layout.addWidget(custom_group)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel);button_box.accepted.connect(self.on_submit);button_box.rejected.connect(self.reject);main_layout.addWidget(button_box)
    def on_submit(self):
        self.new_sheets_data.clear()
        for checkbox in self.standard_sheets_checkboxes:
            if checkbox.isChecked(): dims = checkbox.text().split('x');self.new_sheets_data.append({'name': f"Standard {checkbox.text()}",'width': float(dims[0]), 'height': float(dims[1]),'quantity': 1, 'priority': 1})
        try:
            length = float(self.length_input.text());width = float(self.width_input.text());quantity = int(self.quantity_input.text())
            if length > 0 and width > 0 and quantity > 0: self.new_sheets_data.append({'name': f"Custom {length}x{width}",'width': length, 'height': width,'quantity': quantity, 'priority': 1})
        except (ValueError, TypeError): pass
        self.accept()
    def get_new_sheets(self): return self.new_sheets_data
    def toggle_all_sheets(self, state): is_checked = (state == Qt.CheckState.Checked.value); [cb.setChecked(is_checked) for cb in self.standard_sheets_checkboxes]

# ... (rest of the file remains the same)

# --- 1.9: Interactive Joint Editor ---
class InteractiveJointEditor(QDialog):
    def __init__(self, part_geometry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Interactive Micro-Joint Editor")
        self.setMinimumSize(1000, 600)
        self.part_geometry = part_geometry
        self.joint_points = []
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        preview_panel = QFrame(); preview_layout = QVBoxLayout(preview_panel)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        self.view.setStyleSheet("border: 1px solid #ccc;")
        self.view.setMouseTracking(True)
        self.scene.mousePressEvent = self.scene_mouse_press
        preview_layout.addWidget(QLabel("Click on the part outline to add a micro-joint:"))
        preview_layout.addWidget(self.view)
        settings_panel = QFrame(); settings_layout = QVBoxLayout(settings_panel)
        self.joints_table = QTableWidget()
        self.joints_table.setColumnCount(4)
        self.joints_table.setHorizontalHeaderLabels(["#", "X (mm)", "Y (mm)", "Length (mm)"])
        self.joints_table.setColumnWidth(0, 30)
        settings_layout.addWidget(QLabel("Joint Points:"))
        settings_layout.addWidget(self.joints_table)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        settings_layout.addWidget(button_box)
        splitter.addWidget(preview_panel)
        splitter.addWidget(settings_panel)
        splitter.setSizes([700, 300])
        main_layout.addWidget(splitter)
        self.draw_part()
    def draw_part(self):
        self.scene.clear()
        if self.part_geometry.geom_type == 'Polygon': geometries = [self.part_geometry]
        else: geometries = self.part_geometry.geoms
        for geom in geometries:
            coords = list(geom.exterior.coords)
            q_polygon = QPolygonF([QPointF(x, y) for x, y in coords])
            self.scene.addPolygon(q_polygon, QPen(QColor("#333"), 2))
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
    def scene_mouse_press(self, event):
        pos = event.scenePos()
        marker = QGraphicsEllipseItem(pos.x() - 3, pos.y() - 3, 6, 6)
        marker.setBrush(QBrush(Qt.GlobalColor.red))
        marker.setPen(QPen(Qt.GlobalColor.transparent))
        self.scene.addItem(marker)
        row = self.joints_table.rowCount()
        self.joints_table.insertRow(row)
        self.joints_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.joints_table.setItem(row, 1, QTableWidgetItem(f"{pos.x():.2f}"))
        self.joints_table.setItem(row, 2, QTableWidgetItem(f"{pos.y():.2f}"))
        length_spinbox = QDoubleSpinBox(); length_spinbox.setDecimals(1); length_spinbox.setValue(1.0)
        self.joints_table.setCellWidget(row, 3, length_spinbox)
        self.joint_points.append({'pos': pos, 'length_widget': length_spinbox})
    def get_joint_data(self):
        final_data = []
        for point_data in self.joint_points:
            final_data.append({'x': point_data['pos'].x(), 'y': point_data['pos'].y(), 'length': point_data['length_widget'].value()})
        return final_data

# (LuxuryWelcomePage and PreferencesPage remain unchanged)
class PreferencesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); main_layout = QVBoxLayout(self); main_layout.addWidget(QLabel("Preferences Page Placeholder"))
class LuxuryWelcomePage(QWidget):
    def __init__(self, main_controller=None):
        super().__init__();self.main_controller = main_controller;layout = QVBoxLayout(self);layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label = QLabel("Hyper Nesting");self.title_label.setObjectName("titleLabel");self.new_button = self.create_action_button("  New Project", "fa5s.file-alt")
        self.open_button = self.create_action_button("  Open Project", "fa5s.folder-open");layout.addStretch(2);layout.addWidget(self.title_label);button_layout = QHBoxLayout()
        button_layout.addStretch();button_layout.addWidget(self.new_button);button_layout.addWidget(self.open_button);button_layout.addStretch();layout.addLayout(button_layout);layout.addStretch(3)
        self.setObjectName("mainContent")
        self.setStyleSheet("""
            QWidget#mainContent { background-image: url(https://images.pexels.com/photos/8937637/pexels-photo-8937637.jpeg); background-repeat: no-repeat; background-position: center; border: none; }
            QLabel#titleLabel { color: #DAA520; font-family: 'Segoe UI', Arial, sans-serif; font-size: 70pt; font-weight: bold; background-color: rgba(0, 0, 0, 0.4); border-radius: 15px; padding: 15px 30px; }
        """)
        if self.main_controller: self.new_button.clicked.connect(self.main_controller.show_nesting_window); self.open_button.clicked.connect(self.main_controller.show_nesting_window)
    def create_action_button(self, text, icon_name):
        button = QPushButton(text);button.setIcon(qta.icon(icon_name, color='#FFFFFF'));button.setIconSize(QSize(22, 22));button.setMinimumHeight(45)
        button.setStyleSheet("""
            QPushButton { font-size: 14pt; color: white; background-color: rgba(0, 0, 0, 0.5); border: 1px solid #DAA520; border-radius: 8px; padding: 5px 15px; }
            QPushButton:hover { background-color: rgba(218, 165, 32, 0.5); }
        """);return button