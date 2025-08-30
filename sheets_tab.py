# =============================================================================
#           HyperNesting v3.0 - sheets_tab.py (النسخة النهائية)
# =============================================================================
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTableView, 
                             QFrame, QHBoxLayout, QHeaderView, QAbstractItemView)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta

from ui_components import AddSheetsDialog

class SheetsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 5, 5)
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        self.setup_sheets_table()
        main_layout.addWidget(self.sheets_table_view)

    def create_toolbar(self):
        toolbar_frame = QFrame()
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        toolbar_layout.addWidget(self.create_tool_button("Create Sheet", "fa5s.plus-square", self.create_sheet))
        toolbar_layout.addWidget(self.create_tool_button("DXF/DWG\nCreate", "fa5s.file-import", self.create_from_dxf))
        toolbar_layout.addWidget(self.create_tool_button("Remove\nSelected Sheets", "fa5s.trash-alt", self.remove_selected))
        toolbar_layout.addStretch()
        return toolbar_frame

    def setup_sheets_table(self):
        self.sheets_table_view = QTableView()
        self.sheets_model = QStandardItemModel()
        self.sheets_table_view.setModel(self.sheets_model)
        headers =
        self.sheets_model.setHorizontalHeaderLabels(headers)
        self.sheets_table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.sheets_table_view.verticalHeader().setVisible(False)
        self.sheets_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

    def create_tool_button(self, text, icon_name, function):
        button = QPushButton(f"\n{text}")
        button.setIcon(qta.icon(icon_name, color='#333'))
        button.setIconSize(QSize(32, 32))
        button.setFixedSize(QSize(120, 80))
        button.setStyleSheet("QPushButton { border: none; } QPushButton:hover { background-color: #e0e0e0; border-radius: 5px; }")
        button.clicked.connect(function)
        return button

    def create_sheet(self):
        dialog = AddSheetsDialog(self)
        if dialog.exec():
            new_sheets = dialog.get_new_sheets()
            if new_sheets: self.main_window.add_sheets_from_data(new_sheets)
    
    def create_from_dxf(self): print("'Create Sheet from DXF' button clicked.")
    def remove_selected(self): print("'Remove Selected Sheets' button clicked.")

    def update_table_view(self, sheets_data):
        self.sheets_model.removeRows(0, self.sheets_model.rowCount())
        for sheet in sheets_data:
            row =), QStandardItem(f"{sheet['width']:.2f}"), QStandardItem(f"{sheet['height']:.2f}"),
                   QStandardItem(str(sheet['quantity'])), QStandardItem(str(sheet['priority']))]
            self.sheets_model.appendRow(row)
