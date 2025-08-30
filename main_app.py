# =============================================================================
#           HyperNesting v2.2 - main_app.py (النسخة النهائية والمستقرة)
# =============================================================================
import sys
import os
import random
import time
import concurrent.futures
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

import numpy as np
from shapely.geometry import Polygon, box, Point, LineString
from shapely.ops import unary_union
from shapely.affinity import rotate as shapely_rotate, translate as shapely_translate
import ezdxf
from ezdxf.math import Vec2
import qtawesome as qta

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QVBoxLayout, QPushButton, QLabel, QFrame, QStackedWidget,
                             QTabWidget, QMessageBox, QFileDialog, QProgressDialog)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal

from ui_components import PreferencesPage, LuxuryWelcomePage
from parts_tab import PartsTab
from sheets_tab import SheetsTab
from nesting_tab import NestingTab
from export_tab import ExportTab

# =============================================================================
# ====== القسم 1: عقل البرنامج (الكود الكامل) ======
# =============================================================================
@dataclass
class Part:
    id: str; geometry: Polygon; name: str; source_file: str; quantity: int = 1; placed_geometry: Polygon = None; rotation: float = 0.0
@dataclass
class SheetConfig:
    width: float; height: float; spacing: float; margin: float
@dataclass
class GAConfig:
    # --- THIS LINE IS NOW CORRECTED ---
    population_size: int = 30; generations: int = 20; mutation_rate: float = 0.1; crossover_rate: float = 0.8; allowed_rotations: List[int] = field(default_factory=lambda: [0, 90])
    # ----------------------------------
class NestingEngine:
    def __init__(self, sheet_config: SheetConfig): self.sheet_config = sheet_config; self.sheet_boundary = box(self.sheet_config.margin, self.sheet_config.margin, self.sheet_config.width - self.sheet_config.margin, self.sheet_config.height - self.sheet_config.margin)
    def place_parts(self, parts_to_place: List[Part]) -> Tuple[List[Part], List[Part], float]:
        placed_parts = []; unplaced_parts = []; placed_union = Polygon()
        for part in parts_to_place:
            best_pos = None; min_y, min_x = float('inf'), float('inf'); part_with_spacing = part.geometry.buffer(self.sheet_config.spacing / 2, cap_style=3, join_style=2)
            candidate_points = [Vec2(self.sheet_config.margin, self.sheet_config.margin)]; [candidate_points.extend([Vec2(p.placed_geometry.bounds[2] + self.sheet_config.spacing, p.placed_geometry.bounds[1]), Vec2(p.placed_geometry.bounds[0], p.placed_geometry.bounds[3] + self.sheet_config.spacing)]) for p in placed_parts]
            for pos in candidate_points:
                part_bounds = part_with_spacing.bounds; candidate_geom = shapely_translate(part_with_spacing, xoff=pos.x - part_bounds[0], yoff=pos.y - part_bounds[1])
                if self.sheet_boundary.contains(candidate_geom) and not placed_union.intersects(candidate_geom):
                    if pos.y < min_y or (pos.y == min_y and pos.x < min_x): min_y, min_x = pos.y, pos.x; best_pos = Vec2(pos.x - part_bounds[0], pos.y - part_bounds[1])
            if best_pos: part.placed_geometry = shapely_translate(part.geometry, xoff=best_pos.x, yoff=best_pos.y); placed_parts.append(part); placed_union = unary_union([placed_union, part.placed_geometry.buffer(self.sheet_config.spacing / 2, cap_style=3, join_style=2)])
            else: unplaced_parts.append(part)
        fitness = placed_union.bounds[3] if not placed_union.is_empty else self.sheet_config.height
        return placed_parts, unplaced_parts, fitness
class GeneticAlgorithmNester:
    def __init__(self, parts_pool: List[Part], sheet_config: SheetConfig, ga_config: GAConfig): self.parts_pool = parts_pool; self.sheet_config = sheet_config; self.ga_config = ga_config; self.nesting_engine = NestingEngine(sheet_config)
    def _evaluate_chromosome(self, chromosome: List[Dict]):
        parts_to_place = []
        for gene in chromosome:
            original_part = self.parts_pool[gene['part_index']]; rotated_geom = shapely_rotate(original_part.geometry, gene['rotation'], origin='centroid')
            parts_to_place.append(Part(id=original_part.id, geometry=rotated_geom, name=original_part.name, source_file=original_part.source_file, rotation=gene['rotation']))
        _placed, _unplaced, fitness = self.nesting_engine.place_parts(parts_to_place)
        return fitness + len(_unplaced) * self.sheet_config.width * self.sheet_config.height
    def run(self, progress_callback, should_stop):
        population = []; part_indices = list(range(len(self.parts_pool)))
        for _ in range(self.ga_config.population_size):
            random.shuffle(part_indices); population.append([{'part_index': i, 'rotation': random.choice(self.ga_config.allowed_rotations)} for i in part_indices])
        best_chromosome_overall = population[0]; best_fitness_overall = float('inf')
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for gen in range(self.ga_config.generations):
                if should_stop(): break
                futures = {executor.submit(self._evaluate_chromosome, chrom): chrom for chrom in population}
                results = [(future.result(), futures[future]) for future in concurrent.futures.as_completed(futures)]
                results.sort(key=lambda x: x[0])
                if results[0][0] < best_fitness_overall: best_fitness_overall, best_chromosome_overall = results[0]
                sorted_population = [r[1] for r in results]; next_generation = sorted_population[:2]
                while len(next_generation) < self.ga_config.population_size:
                    p1, p2 = random.choices(sorted_population[:len(sorted_population)//2], k=2)
                    crossover_point = random.randint(1, len(p1) - 1); child_order = [g['part_index'] for g in p1[:crossover_point]]; child_order.extend([g['part_index'] for g in p2 if g['part_index'] not in child_order])
                    child = [{'part_index': i, 'rotation': random.choice(self.ga_config.allowed_rotations)} for i in child_order]
                    if random.random() < self.ga_config.mutation_rate: idx1, idx2 = random.sample(range(len(child)), 2); child[idx1], child[idx2] = child[idx2], child[idx1]
                    next_generation.append(child)
                population = next_generation; progress_callback(int((gen + 1) / self.ga_config.generations * 100))
        final_parts_to_place = []
        for gene in best_chromosome_overall:
            original_part = self.parts_pool[gene['part_index']]; rotated_geom = shapely_rotate(original_part.geometry, gene['rotation'], origin='centroid')
            final_parts_to_place.append(Part(id=original_part.id, geometry=rotated_geom, name=original_part.name, source_file=original_part.source_file, rotation=gene['rotation']))
        return self.nesting_engine.place_parts(final_parts_to_place)

class NestingWorker(QThread):
    finished = pyqtSignal(object); progress = pyqtSignal(int); log = pyqtSignal(str)
    def __init__(self, parts, sheet_config, ga_config):
        super().__init__(); self.parts = parts; self.sheet_config = sheet_config; self.ga_config = ga_config
        self._is_cancelled = False
    def run(self):
        try:
            self.log.emit("Starting Full Genetic Algorithm..."); start_time = time.time()
            ga_nester = GeneticAlgorithmNester(self.parts, self.sheet_config, self.ga_config)
            placed, unplaced, fitness = ga_nester.run(lambda p: self.progress.emit(p), lambda: self._is_cancelled)
            if self._is_cancelled: self.log.emit("Nesting process cancelled by user."); return
            duration = time.time() - start_time
            self.log.emit(f"Process finished in {duration:.2f} seconds.")
            self.finished.emit({"placed": placed, "unplaced": unplaced, "fitness": fitness})
        except Exception as e: self.log.emit(f"Error in worker thread: {e}"); self.finished.emit(None)
    def cancel(self): self._is_cancelled = True

class NestingMainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("مساحة عمل التعشيق"); self.setWindowFlags(Qt.WindowType.Widget)
        self.parts_data: List[Dict] = []; self.sheets_data: List[Dict] = []; self.nesting_results = []
        self.unique_parts_geometry = set(); self.worker = None; self.progress_dialog = None
        self.tabs = QTabWidget(); self.setCentralWidget(self.tabs)
        self.parts_tab = PartsTab(self); self.sheets_tab = SheetsTab(self); self.nesting_tab = NestingTab(self); self.export_tab = ExportTab(self)
        self.tabs.addTab(self.parts_tab, "Parts"); self.tabs.addTab(self.sheets_tab, "Sheets"); self.tabs.addTab(self.nesting_tab, "Nesting"); self.tabs.addTab(self.export_tab, "Export")

    def apply_manual_micro_joints(self, all_joints_data: Dict):
        for row_index, joints in all_joints_data.items():
            if row_index >= len(self.parts_data): continue
            part_geometry = self.parts_data[row_index]['geometry']
            if part_geometry.geom_type != 'Polygon': continue
            boundary = part_geometry.exterior
            for joint in joints:
                joint_point = Point(joint['x'], joint['y']); joint_length = joint['length']
                cutter = joint_point.buffer(joint_length / 2, cap_style=3)
                boundary = boundary.difference(cutter)
            new_polygon = Polygon(boundary)
            self.parts_data[row_index]['geometry'] = new_polygon
        self.parts_tab.update_table_view(self.parts_data)
        last_row = list(all_joints_data.keys())[-1]
        self.parts_tab.parts_table_view.selectRow(last_row)
        QMessageBox.information(self, "نجاح", "تم تطبيق الوصلات الدقيقة بنجاح.")

    def import_dxf_files(self, filepaths: List[str]):
        parts_found_in_this_import = 0
        for filepath in filepaths:
            try:
                doc = ezdxf.readfile(filepath); msp = doc.modelspace()
                entities = msp.query('LINE ARC CIRCLE ELLIPSE SPLINE LWPOLYLINE POLYLINE')
                geoms = ezdxf.geom.construct_entities(entities); polygons = list(ezdxf.geom.polygonize(geoms))
                for i, poly_points in enumerate(polygons):
                    points = [(p.x, p.y) for p in poly_points]
                    if len(points) > 2:
                        shapely_poly = Polygon(points); geom_wkt = shapely_poly.wkt
                        if shapely_poly.is_valid and shapely_poly.area > 1e-6 and geom_wkt not in self.unique_parts_geometry:
                            self.unique_parts_geometry.add(geom_wkt); part_name = f"{os.path.basename(filepath).split('.')[0]}_{i+1}"
                            self.parts_data.append({'name': part_name, 'geometry': shapely_poly, 'quantity': 1, 'rotation': 0}); parts_found_in_this_import += 1
            except Exception as e: QMessageBox.critical(self, "خطأ في الاستيراد", f"فشل في معالجة الملف {filepath}:\n{e}")
        if parts_found_in_this_import > 0:
            self.parts_tab.update_table_view(self.parts_data)
            QMessageBox.information(self, "نجاح", f"تمت إضافة {parts_found_in_this_import} قطعة جديدة بنجاح.")
        else: QMessageBox.warning(self, "لا توجد قطع جديدة", "لم يتم العثور على أي أشكال مغلقة جديدة أو غير مكررة.")

    def remove_selected_parts(self, selected_rows):
        if not selected_rows: QMessageBox.warning(self, "لا يوجد تحديد", "الرجاء تحديد القطع التي تريد حذفها أولاً."); return
        reply = QMessageBox.question(self, "تأكيد الحذف", f"هل أنت متأكد من أنك تريد حذف {len(selected_rows)} قطعة؟", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            indices_to_delete = sorted([r.row() for r in selected_rows], reverse=True)
            for index in indices_to_delete:
                part_to_remove = self.parts_data.pop(index); self.unique_parts_geometry.remove(part_to_remove['geometry'].wkt)
            self.parts_tab.update_table_view(self.parts_data)

    def start_nesting(self, params: Dict):
        if self.worker and self.worker.isRunning(): QMessageBox.warning(self, "عملية جارية", "الرجاء الانتظار حتى تنتهي عملية التعشيش الحالية."); return
        parts_to_nest_pool = [Part(id=part_data['name'], name=part_data['name'], geometry=part_data['geometry'], source_file='') for part_data in self.parts_data for _ in range(part_data['quantity'])]
        if not parts_to_nest_pool: QMessageBox.warning(self, "لا توجد قطع", "الرجاء إضافة قطع أولًا."); return
        sheet_config = SheetConfig(width=params['sheet_width'], height=params['sheet_height'], spacing=params['part_spacing'], margin=params['sheet_margin'])
        ga_config = GAConfig()
        self.progress_dialog = QProgressDialog("جاري عملية التعشيش...", "إلغاء", 0, 100, self)
        self.progress_dialog.canceled.connect(self.cancel_nesting); self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.sheet_width = params['sheet_width']; self.progress_dialog.sheet_height = params['sheet_height']
        self.progress_dialog.show()
        self.worker = NestingWorker(parts_to_nest_pool, sheet_config, ga_config)
        self.worker.finished.connect(self.on_nesting_finished); self.worker.progress.connect(self.progress_dialog.setValue); self.worker.log.connect(print); self.worker.start()
        self.nesting_tab.toggle_buttons(False)

    def cancel_nesting(self):
        if self.worker and self.worker.isRunning(): self.worker.cancel()

    def on_nesting_finished(self, result: Dict):
        self.progress_dialog.close(); self.nesting_tab.toggle_buttons(True)
        if not result:
            if not (self.worker and self.worker._is_cancelled): QMessageBox.critical(self, "فشل", "فشلت عملية التعشيش.")
        else:
            final_layout = result['placed']; sheet_area = self.progress_dialog.sheet_width * self.progress_dialog.sheet_height
            efficiency = (sum(p.geometry.area for p in final_layout) / sheet_area) * 100 if final_layout and sheet_area > 0 else 0
            self.nesting_results = [{'rank': 1, 'util': efficiency, 'parts_nested': f"{len(final_layout)} of {len(final_layout) + len(result['unplaced'])}", 'time': "N/A",
                'layout': [{'name': f"Sheet {self.progress_dialog.sheet_width}x{self.progress_dialog.sheet_height}", 'width': self.progress_dialog.sheet_width, 'height': self.progress_dialog.sheet_height, 'util': efficiency, 'placed_parts_geometries': final_layout }]}]
            self.nesting_tab.update_results(self.nesting_results)
            QMessageBox.information(self, "نجاح", f"اكتمل التعشيش! تم وضع {len(final_layout)} قطعة.")
    def add_sheets_from_data(self, new_sheets): self.sheets_data.extend(new_sheets); self.sheets_tab.update_table_view(self.sheets_data)

class MainController(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Hyper Nesting v2.2"); self.setGeometry(50, 50, 1366, 768); self.setWindowIcon(qta.icon("fa5s.cogs", color='#DAA520'))
        main_widget = QWidget(); main_layout = QHBoxLayout(main_widget); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        sidebar = self.create_sidebar(); main_layout.addWidget(sidebar); self.stacked_widget = QStackedWidget(); main_layout.addWidget(self.stacked_widget, 1)
        self.welcome_page = LuxuryWelcomePage(self); self.preferences_page = PreferencesPage(self); self.nesting_page = NestingMainWindow()
        self.stacked_widget.addWidget(self.welcome_page); self.stacked_widget.addWidget(self.preferences_page); self.stacked_widget.addWidget(self.nesting_page)
        self.setCentralWidget(main_widget); self.show_welcome_page()
    def create_sidebar(self):
        sidebar = QFrame(); sidebar.setFixedWidth(250); sidebar.setStyleSheet("background-color: #121212;"); sidebar_layout = QVBoxLayout(sidebar); sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar_layout.setContentsMargins(0, 20, 0, 20); sidebar_layout.setSpacing(5); welcome_button = self.create_sidebar_button("Welcome", "fa5s.home"); new_button = self.create_sidebar_button("New", "fa5s.file-alt");open_button = self.create_sidebar_button("Open", "fa5s.folder-open"); save_button = self.create_sidebar_button("Save", "fa5s.save");save_as_button = self.create_sidebar_button("Save As", "fa5s.save"); preferences_button = self.create_sidebar_button("Preferences", "fa5s.cog");exit_button = self.create_sidebar_button("Exit", "fa5s.times-circle")
        sidebar_layout.addWidget(welcome_button); sidebar_layout.addWidget(new_button); sidebar_layout.addWidget(open_button); sidebar_layout.addWidget(save_button); sidebar_layout.addWidget(save_as_button); sidebar_layout.addWidget(preferences_button); sidebar_layout.addStretch(); sidebar_layout.addWidget(exit_button)
        welcome_button.clicked.connect(self.show_welcome_page); preferences_button.clicked.connect(self.show_preferences_page); new_button.clicked.connect(self.show_nesting_window); open_button.clicked.connect(self.show_nesting_window); exit_button.clicked.connect(self.close); return sidebar
    def create_sidebar_button(self, text, icon_name):
        button = QPushButton(f"  {text}"); button.setIcon(qta.icon(icon_name, color='#DAA520')); button.setIconSize(QSize(20, 20)); button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet("QPushButton { color: #DAA520; background-color: transparent; border: none; padding: 12px 20px; text-align: left; font-size: 12pt; } QPushButton:hover { background-color: #282828; }"); return button
    def show_welcome_page(self): self.stacked_widget.setCurrentWidget(self.welcome_page)
    def show_preferences_page(self): self.stacked_widget.setCurrentWidget(self.preferences_page)
    def show_nesting_window(self): self.stacked_widget.setCurrentWidget(self.nesting_page)

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        import multiprocessing
        multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    controller = MainController()
    controller.show()
    sys.exit(app.exec())