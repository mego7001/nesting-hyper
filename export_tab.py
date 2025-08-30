# =============================================================================
#           HyperNesting v3.0 - export_tab.py (النسخة النهائية)
# =============================================================================
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QFrame, 
                             QHBoxLayout, QLabel, QFileDialog)
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta

from ui_components import DxfExportDialog, SummaryReportViewer, DetailedReportViewer

class ExportTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 5, 5)
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        self.results_display = QLabel("Press a button above to export the nesting results.", alignment=Qt.AlignmentFlag.AlignCenter)
        self.results_display.setStyleSheet("font-size: 16px; color: gray;")
        main_layout.addWidget(self.results_display)

    def create_toolbar(self):
        toolbar_frame = QFrame()
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        toolbar_layout.addWidget(self.create_tool_button("DXF/DWG\nExport", "fa5s.file-export", self.open_dxf_export_dialog))
        toolbar_layout.addWidget(self.create_tool_button("Summary\nReport", "fa5s.file-alt", self.open_summary_report))
        toolbar_layout.addWidget(self.create_tool_button("Detailed\nReport", "fa5s.file-invoice", self.open_detailed_report))
        toolbar_layout.addStretch()
        return toolbar_frame

    def create_tool_button(self, text, icon_name, function):
        button = QPushButton(f"\n{text}")
        button.setIcon(qta.icon(icon_name, color='#333'))
        button.setIconSize(QSize(32, 32))
        button.setFixedSize(QSize(120, 80))
        button.setStyleSheet("QPushButton { border: none; } QPushButton:hover { background-color: #e0e0e0; border-radius: 5px; }")
        button.clicked.connect(function)
        return button

    def open_dxf_export_dialog(self):
        if not self.main_window.nesting_results: print("No nesting results to export."); return
        dialog = DxfExportDialog(self)
        if dialog.exec():
            settings = dialog.get_settings(); print("--- DXF Export Settings ---\n", json.dumps(settings, indent=2))
            file_path, _ = QFileDialog.getSaveFileName(self, "Save CAD Layout", "", "DXF Files (*.dxf)")
            if file_path: print(f"File would be saved to: {file_path}")

    def open_summary_report(self):
        if not self.main_window.nesting_results: print("No nesting results for summary report."); return
        mock_data = {"job_summary": { "nests": len(self.main_window.nesting_results) }, "sheet_requirements":, "parts_list":}
        self.summary_report_viewer = SummaryReportViewer(mock_data, self); self.summary_report_viewer.show()

    def open_detailed_report(self):
        if not self.main_window.nesting_results: print("No nesting results for detailed report."); return
        first_result = self.main_window.nesting_results
        placed_parts_data =
        if 'placed_parts_geometries' in first_result['layout']:
            for part in first_result['layout']['placed_parts_geometries']: placed_parts_data.append({'name': part.name})
        mock_data = {"header_summary": { "nest_no": "1 of X" }, "main_preview": first_result['layout'], "parts_list": placed_parts_data, "footer": {}}
        self.detailed_report_viewer = DetailedReportViewer(mock_data, self); self.detailed_report_viewer.show()
