# =============================================================================
#           HyperNesting v3.0 - nesting_tab.py (النسخة النهائية)
# =============================================================================
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QSplitter,
                             QTableView, QTreeWidget, QTreeWidgetItem,
                             QGraphicsView, QGraphicsScene, QGroupBox, QRadioButton,
                             QFormLayout, QDoubleSpinBox, QGridLayout)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor, QPen, QPolygonF
from PyQt6.QtCore import Qt, QSize, QPointF
import qtawesome as qta

class NestingTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        self.toolbar = self.create_toolbar()
        main_layout.addWidget(self.toolbar)
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)
        results_splitter = QSplitter(Qt.Orientation.Vertical)
        self.setup_results_table()
        results_splitter.addWidget(self.results_table_view)
        bottom_panel = QWidget(); bottom_layout = QVBoxLayout(bottom_panel)
        details_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setup_placed_parts_tree(); self.setup_efficiency_graph()
        details_splitter.addWidget(self.placed_parts_tree); details_splitter.addWidget(self.efficiency_view)
        details_splitter.setSizes()
        bottom_layout.addWidget(details_splitter); bottom_layout.addWidget(QLabel("Current Layout"))
        self.setup_layout_preview(); bottom_layout.addWidget(self.layout_preview_view)
        results_splitter.addWidget(bottom_panel); results_splitter.setSizes()
        main_layout.addWidget(results_splitter)
        self.toggle_buttons(True)

    def on_result_selected(self, selected, deselected):
        indexes = selected.indexes()
        if not indexes: return
        result_data = self.main_window.nesting_results[indexes.row()]
        self.placed_parts_tree.clear()
        if 'placed_parts_geometries' in result_data['layout']:
             for part_obj in result_data['layout']['placed_parts_geometries']:
                 QTreeWidgetItem(self.placed_parts_tree,)
        self.efficiency_scene.clear(); util = result_data['util']
        self.efficiency_scene.addRect(10, 10, 200, 30, QPen(QColor("lightgreen")), QBrush(QColor("lightgreen")))
        self.efficiency_scene.addRect(10, 10, 2 * util, 30, QPen(QColor("darkgreen")), QBrush(QColor("green")))
        self.efficiency_scene.addText(f"{util:.2f}%").setPos(90, 15)
        self.layout_preview_scene.clear()
        layout_info = result_data['layout']
        sheet_w, sheet_h = layout_info['width'], layout_info['height']
        self.layout_preview_scene.addRect(0, 0, sheet_w, sheet_h, QPen(QColor("gray")))
        placed_parts_geometries = layout_info.get('placed_parts_geometries',)
        for part_obj in placed_parts_geometries:
            if part_obj.placed_geometry:
                # للتعامل مع الأشكال التي تم تعديلها (قد تكون MultiLineString)
                if hasattr(part_obj.placed_geometry, 'geoms'):
                    for geom in part_obj.placed_geometry.geoms:
                        coords = list(geom.coords)
                        q_polygon = QPolygonF([QPointF(x, y) for x, y in coords])
                        self.layout_preview_scene.addPolygon(q_polygon, QPen(Qt.GlobalColor.black), QBrush(QColor("lightblue")))
                else:
                    coords = list(part_obj.placed_geometry.exterior.coords)
                    q_polygon = QPolygonF([QPointF(x, y) for x, y in coords])
                    self.layout_preview_scene.addPolygon(q_polygon, QPen(Qt.GlobalColor.black), QBrush(QColor("lightblue")))
        self.layout_preview_view.fitInView(self.layout_preview_scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def create_toolbar(self):
        self.start_button = self.create_tool_button("Start", "fa5s.play-circle", self.start_nesting, icon_size=QSize(24, 24), fixed_size=QSize(80, 40))
        self.stop_button = self.create_tool_button("Stop", "fa5s.stop-circle", self.stop_nesting, icon_size=QSize(24, 24), fixed_size=QSize(80, 40))
        toolbar_frame = QFrame(); toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        start_stop_layout = QVBoxLayout(); start_stop_layout.addWidget(self.start_button); start_stop_layout.addWidget(self.stop_button)
        toolbar_layout.addLayout(start_stop_layout)
        toolbar_layout.addWidget(self.create_separator())
        settings_layout = QFormLayout()
        self.part_spacing_spin = QDoubleSpinBox(); self.part_spacing_spin.setValue(10.0)
        self.sheet_margin_spin = QDoubleSpinBox(); self.sheet_margin_spin.setValue(15.0)
        self.sheet_width_spin = QDoubleSpinBox(); self.sheet_width_spin.setRange(1, 99999); self.sheet_width_spin.setValue(2440)
        self.sheet_height_spin = QDoubleSpinBox(); self.sheet_height_spin.setRange(1, 99999); self.sheet_height_spin.setValue(1220)
        settings_layout.addRow("Part Spacing:", self.part_spacing_spin)
        settings_layout.addRow("Sheet Margin:", self.sheet_margin_spin)
        settings_layout.addRow("Sheet Width:", self.sheet_width_spin)
        settings_layout.addRow("Sheet Height:", self.sheet_height_spin)
        toolbar_layout.addLayout(settings_layout); toolbar_layout.addStretch()
        return toolbar_frame

    def toggle_buttons(self, enabled):
        self.start_button.setEnabled(enabled)
        self.stop_button.setEnabled(not enabled)
        
    def setup_results_table(self):
        self.results_table_view = QTableView()
        self.results_model = QStandardItemModel()
        self.results_table_view.setModel(self.results_model)
        headers =; self.results_model.setHorizontalHeaderLabels(headers)
        self.results_table_view.selectionModel().selectionChanged.connect(self.on_result_selected)

    def setup_placed_parts_tree(self): self.placed_parts_tree = QTreeWidget(); self.placed_parts_tree.setHeaderLabels()
    def setup_efficiency_graph(self): self.efficiency_scene = QGraphicsScene(); self.efficiency_view = QGraphicsView(self.efficiency_scene)
    def setup_layout_preview(self): self.layout_preview_scene = QGraphicsScene(); self.layout_preview_view = QGraphicsView(self.layout_preview_scene)

    def create_tool_button(self, text, icon_name, function, icon_size=QSize(24, 24), fixed_size=None):
        button = QPushButton(f" {text}"); button.setIcon(qta.icon(icon_name, color='#333')); button.setIconSize(icon_size)
        if fixed_size: button.setFixedSize(fixed_size)
        button.clicked.connect(function); return button

    def create_separator(self): sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine); sep.setFrameShadow(QFrame.Shadow.Sunken); return sep

    def start_nesting(self):
        params = {
            'part_spacing': self.part_spacing_spin.value(), 'sheet_margin': self.sheet_margin_spin.value(),
            'sheet_width': self.sheet_width_spin.value(), 'sheet_height': self.sheet_height_spin.value()
        }
        self.main_window.start_nesting(params)

    def stop_nesting(self): self.main_window.cancel_nesting()

    def update_results(self, results_data):
        self.results_model.removeRows(0, self.results_model.rowCount())
        for res in results_data:
            row =)), QStandardItem(f"{res['util']:.2f}"), QStandardItem(res['parts_nested']), QStandardItem(res['time'])]
            self.results_model.appendRow(row)
        if self.results_model.rowCount() > 0: self.results_table_view.selectRow(0)
