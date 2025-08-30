# =============================================================================
#           HyperNesting v3.0 - parts_tab.py (النسخة النهائية والمُصححة)
# =============================================================================
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QFrame, QSplitter, QLabel, QFileDialog,
                             QTableWidget, QGraphicsScene, QGraphicsView, QSpinBox, QHeaderView, QAbstractItemView, QMessageBox, QTableWidgetItem)
from PyQt6.QtGui import QFont, QColor, QPen, QBrush, QPolygonF
from PyQt6.QtCore import Qt, QSize, QPointF
import qtawesome as qta
from ui_components import InteractiveJointEditor

class PartsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 5, 5, 0)
        toolbar = self.create_toolbar()
        self.setup_parts_table()
        bottom_bar = self.setup_bottom_bar()
        left_layout.addWidget(toolbar)
        left_layout.addWidget(self.parts_table_view)
        left_layout.addWidget(bottom_bar)
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 0, 0)
        self.setup_preview_panel()
        self.setup_stats_panel()
        right_layout.addWidget(self.preview_panel, 3)
        right_layout.addWidget(self.stats_panel, 1)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        # splitter.setSizes() # You may need to set sizes e.g., splitter.setSizes([700, 300])
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(splitter)
        self.show_preview_placeholder()
    
    def open_auto_joint_dialog(self):
        selected_rows_indices = self.parts_table_view.selectionModel().selectedRows()
        if not selected_rows_indices:
            QMessageBox.warning(self, "خطأ", "الرجاء تحديد قطعة واحدة على الأقل لفتح محرر الوصلات.")
            return

        # تم الإصلاح: إعادة كتابة هذا الجزء بالكامل بتنسيق صحيح ومنطقي
        row_indices_to_update = []
        all_joints_data = {}
        
        for index in selected_rows_indices:
            row = index.row()
            part_data = self.main_window.parts_data[row]
            # Assuming editor should be opened for each part
            editor = InteractiveJointEditor(part_data['geometry'], self)
            if editor.exec():
                joint_data = editor.get_joint_data()
                if joint_data:
                    row_indices_to_update.append(row)
                    all_joints_data[row] = joint_data
                    
        if row_indices_to_update:
            self.main_window.apply_manual_micro_joints(all_joints_data)
    
    def add_dxf_files(self):
        filepaths, _ = QFileDialog.getOpenFileNames(self.main_window, "اختر ملفات DXF", "", "DXF Files (*.dxf)")
        if filepaths:
            self.main_window.import_dxf_files(filepaths)
        
    def remove_parts(self):
        selected_rows = self.parts_table_view.selectionModel().selectedRows()
        if selected_rows:
            self.main_window.remove_selected_parts(selected_rows)

    def on_selection_changed(self, selected, deselected):
        indexes = self.parts_table_view.selectionModel().selectedRows()
        if not indexes:
            self.show_preview_placeholder()
            return
        
        # We take the first selected row for the preview
        part_data = self.main_window.parts_data[indexes[0].row()]
        self.preview_scene.clear()
        polygon_geom = part_data['geometry']
        
        geometries = []
        if polygon_geom.geom_type == 'Polygon':
            geometries = [polygon_geom]
        elif polygon_geom.geom_type == 'MultiPolygon':
            geometries = polygon_geom.geoms
        
        for geom in geometries:
            coords = list(geom.exterior.coords)
            q_polygon = QPolygonF([QPointF(x, y) for x, y in coords])
            bounding_rect = q_polygon.boundingRect()
            # Center the polygon in the view
            q_polygon.translate(-bounding_rect.center())
            self.preview_scene.addPolygon(q_polygon, QPen(Qt.GlobalColor.black), QBrush(QColor("#ff6347")))
            
        self.preview_view.fitInView(self.preview_scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def on_quantity_changed(self, value, row_index):
        if row_index < len(self.main_window.parts_data):
            self.main_window.parts_data[row_index]['quantity'] = value
            total_quantity = sum(part['quantity'] for part in self.main_window.parts_data)
            self.total_parts_label.setText(f"Total for Nesting = {total_quantity}")

    def update_table_view(self, parts_data):
        self.parts_table_view.setRowCount(0)
        if not parts_data: return
        
        total_quantity = sum(part['quantity'] for part in parts_data)
        self.parts_table_view.setRowCount(len(parts_data))

        for i, part in enumerate(parts_data):
            bounds = part['geometry'].bounds  # (minx, miny, maxx, maxy)
            # تم الإصلاح: طريقة حساب العرض والارتفاع
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            
            self.parts_table_view.setItem(i, 0, QTableWidgetItem(part['name']))
            self.parts_table_view.setItem(i, 1, QTableWidgetItem(f"{width:.2f}"))
            self.parts_table_view.setItem(i, 2, QTableWidgetItem(f"{height:.2f}"))
            
            quantity_spinbox = QSpinBox()
            quantity_spinbox.setMinimum(1)
            quantity_spinbox.setMaximum(9999)
            quantity_spinbox.setValue(part['quantity'])
            quantity_spinbox.valueChanged.connect(lambda val, index=i: self.on_quantity_changed(val, index))
            self.parts_table_view.setCellWidget(i, 3, quantity_spinbox)
            
            self.parts_table_view.setItem(i, 4, QTableWidgetItem(str(part.get('rotation', 0))))
            
        self.total_parts_label.setText(f"Total for Nesting = {total_quantity}")
        self.unique_parts_label.setText(f"Unique Parts = {len(parts_data)}")

    def create_toolbar(self):
        toolbar_frame = QFrame()
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        toolbar_layout.addWidget(self.create_tool_button("Import Parts", "fa5s.file-import", self.add_dxf_files))
        toolbar_layout.addWidget(self.create_tool_button("Remove Selected", "fa5s.trash-alt", self.remove_parts))
        toolbar_layout.addWidget(self.create_tool_button("Micro Joint", "fa5s.thumbtack", self.open_auto_joint_dialog))
        return toolbar_frame

    def setup_parts_table(self):
        self.parts_table_view = QTableWidget()
        self.parts_table_view.setColumnCount(5)
        # تم الإصلاح: إضافة العناوين الناقصة
        headers = ["Part Name", "Width", "Height", "Quantity", "Rotation"]
        self.parts_table_view.setHorizontalHeaderLabels(headers)
        self.parts_table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.parts_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.parts_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.parts_table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def show_preview_placeholder(self):
        self.preview_scene.clear()
        font = QFont("Arial", 14)
        text_item = self.preview_scene.addText("Select a part to preview...", font)
        text_item.setDefaultTextColor(QColor("gray"))
        # Center the placeholder text
        scene_rect = self.preview_scene.sceneRect()
        text_rect = text_item.boundingRect()
        text_item.setPos((scene_rect.width() - text_rect.width()) / 2, (scene_rect.height() - text_rect.height()) / 2)

    def setup_bottom_bar(self):
        bottom_frame = QFrame()
        bottom_layout = QHBoxLayout(bottom_frame)
        self.unique_parts_label = QLabel("Unique Parts = 0")
        self.total_parts_label = QLabel("Total for Nesting = 0")
        bottom_layout.addWidget(self.unique_parts_label)
        bottom_layout.addWidget(self.total_parts_label)
        bottom_layout.addStretch()
        return bottom_frame

    def setup_preview_panel(self):
        self.preview_panel = QFrame()
        self.preview_panel.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self.preview_panel)
        self.preview_scene = QGraphicsScene()
        self.preview_view = QGraphicsView(self.preview_scene)
        self.preview_view.setRenderHint(self.preview_view.renderHints().Antialiasing)
        layout.addWidget(self.preview_view)

    def setup_stats_panel(self):
        self.stats_panel = QFrame()
        self.stats_panel.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self.stats_panel)
        self.stats_table = QTableWidget(1, 3)
        # تم الإصلاح: إضافة عناوين افتراضية للجدول
        self.stats_table.setHorizontalHeaderLabels(["Statistic", "Value", "Unit"])
        layout.addWidget(self.stats_table)

    def create_tool_button(self, text, icon_name, function, fixed_size=QSize(120, 80)):
        button = QPushButton(f"\n{text}")
        button.setIcon(qta.icon(icon_name, color='#333'))
        button.setIconSize(QSize(32, 32))
        if fixed_size:
            button.setFixedSize(fixed_size)
        button.setStyleSheet("QPushButton { border: none; font-weight: bold; } QPushButton:hover { background-color: #e0e0e0; border-radius: 5px; }")
        button.clicked.connect(function)
        return button