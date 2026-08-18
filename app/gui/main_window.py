from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QProgressBar, QMessageBox, QFileDialog,
                               QComboBox, QCheckBox, QDialog)
from PySide6.QtCore import Qt
import logging
import os
from app.gui.connection_dialog import ConnectionDialog
from app.gui.workers import CompareWorker
from app.transfer.uploader import UploaderWorker
from app.database.models import ComparisonResult
from app.database.cache import FileCache
from app.export.exporters import Exporter
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synology File Comparator")
        self.resize(1100, 750)
        
        self.synology_client = None
        self.worker = None
        self.all_results = []
        self.cache = FileCache()
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # --- Connection Section ---
        conn_layout = QHBoxLayout()
        self.lbl_status = QLabel("Estado: No conectado")
        self.lbl_status.setStyleSheet("color: red; font-weight: bold;")
        self.btn_connect = QPushButton("Conectar a NAS")
        self.btn_connect.clicked.connect(self.open_connection_dialog)
        conn_layout.addWidget(self.lbl_status)
        conn_layout.addStretch()
        conn_layout.addWidget(self.btn_connect)
        main_layout.addLayout(conn_layout)
        
        # --- Paths Section ---
        path_layout = QVBoxLayout()
        
        # Local
        loc_layout = QHBoxLayout()
        loc_layout.addWidget(QLabel("Carpeta Local:"))
        self.txt_local = QLineEdit()
        loc_layout.addWidget(self.txt_local)
        btn_browse = QPushButton("Examinar")
        btn_browse.clicked.connect(self.browse_local)
        loc_layout.addWidget(btn_browse)
        path_layout.addLayout(loc_layout)
        
        # NAS
        nas_layout = QHBoxLayout()
        nas_layout.addWidget(QLabel("Carpeta NAS:"))
        self.txt_nas = QLineEdit()
        self.txt_nas.setPlaceholderText("Ej: /Documentos/Proyecto")
        nas_layout.addWidget(self.txt_nas)
        path_layout.addLayout(nas_layout)
        
        main_layout.addLayout(path_layout)
        
        # --- Action ---
        action_layout = QHBoxLayout()
        self.btn_compare = QPushButton("COMPARAR ARCHIVOS")
        self.btn_compare.setMinimumHeight(40)
        self.btn_compare.setStyleSheet("font-weight: bold; background-color: #4CAF50; color: white;")
        self.btn_compare.clicked.connect(self.start_comparison)
        self.btn_compare.setEnabled(False) # Needs connection
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setMinimumHeight(40)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_comparison)
        
        # Checkboxes options
        options_layout = QVBoxLayout()
        self.chk_use_cache = QCheckBox("Usar Caché (Ignorar remoto si no cambió localmente)")
        self.chk_use_cache.setChecked(True)
        self.chk_deep_verify = QCheckBox("Verificación Profunda (MD5) - Puede ser lento")
        options_layout.addWidget(self.chk_use_cache)
        options_layout.addWidget(self.chk_deep_verify)
        
        action_layout.addWidget(self.btn_compare)
        action_layout.addWidget(self.btn_cancel)
        action_layout.addLayout(options_layout)
        main_layout.addLayout(action_layout)
        
        # --- Filters and Export ---
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar por Estado:"))
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItems(["Todos", "FALTANTE", "DIFERENTE", "SOLO_NAS", "OK"])
        self.cmb_filter.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.cmb_filter)
        
        filter_layout.addStretch()
        
        self.btn_export_csv = QPushButton("Exportar CSV")
        self.btn_export_csv.clicked.connect(self.export_csv)
        self.btn_export_excel = QPushButton("Exportar Excel")
        self.btn_export_excel.clicked.connect(self.export_excel)
        filter_layout.addWidget(self.btn_export_csv)
        filter_layout.addWidget(self.btn_export_excel)
        main_layout.addLayout(filter_layout)
        
        # --- Transfer ---
        transfer_layout = QHBoxLayout()
        transfer_layout.addWidget(QLabel("Sobrescribir:"))
        self.cmb_overwrite = QComboBox()
        self.cmb_overwrite.addItems(["NO", "SI"])
        transfer_layout.addWidget(self.cmb_overwrite)
        
        self.btn_upload = QPushButton("Subir archivos faltantes")
        self.btn_upload.setStyleSheet("font-weight: bold; background-color: #2196F3; color: white;")
        self.btn_upload.clicked.connect(self.start_upload)
        self.btn_upload.setEnabled(False)
        transfer_layout.addWidget(self.btn_upload)
        
        main_layout.addLayout(transfer_layout)
        
        # --- Progress ---
        self.lbl_progress = QLabel("Progreso: 0%")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.lbl_progress)
        main_layout.addWidget(self.progress_bar)
        
        # --- Summary ---
        self.lbl_summary = QLabel("")
        self.lbl_summary.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.lbl_summary)
        
        # --- Results Table ---
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Estado", "Ruta", "Tamaño Local", "Tamaño NAS", "Fecha Local", "Fecha NAS"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        main_layout.addWidget(self.table)

    def open_connection_dialog(self):
        dialog = ConnectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.synology_client = dialog.client
            self.lbl_status.setText("Estado: Conectado")
            self.lbl_status.setStyleSheet("color: green; font-weight: bold;")
            self.btn_compare.setEnabled(True)
            
    def browse_local(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta local")
        if folder:
            self.txt_local.setText(folder)
            
    def start_comparison(self):
        local_path = self.txt_local.text().strip()
        remote_path = self.txt_nas.text().strip()
        
        # Clean the remote path if the user included /volumeX/
        import re
        remote_path = re.sub(r'^/volume\d+/', '/', remote_path)
        
        if not local_path or not os.path.exists(local_path):
            QMessageBox.warning(self, "Error", "Ruta local inválida.")
            return
            
        if not remote_path:
            QMessageBox.warning(self, "Error", "Debe especificar una ruta del NAS.")
            return
            
        self.btn_compare.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.table.setRowCount(0)
        self.lbl_summary.setText("Escaneando...")
        self.progress_bar.setValue(0)
        
        use_cache = self.chk_use_cache.isChecked()
        deep_verify = self.chk_deep_verify.isChecked()
        
        self.worker = CompareWorker(self.synology_client, local_path, remote_path, use_cache, deep_verify, self.cache)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.comparison_finished)
        self.worker.error.connect(self.comparison_error)
        self.worker.start()
        
    def cancel_comparison(self):
        if self.worker:
            self.worker.is_cancelled = True
            self.worker.wait()
            self.update_progress("Cancelado por el usuario", 0)
            self.btn_compare.setEnabled(True)
            self.btn_cancel.setEnabled(False)

    def update_progress(self, msg: str, val: int):
        self.lbl_progress.setText(msg)
        if val == -1:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(val)
        
    def comparison_finished(self, results: list):
        self.btn_compare.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_upload.setEnabled(True)
        
        self.all_results = results
        logging.info(f"Comparación finalizada. {len(results)} archivos procesados.")
        
        self.update_progress("Renderizando resultados en la tabla...", -1)
        
        # Give UI a moment to show the message before doing the heavy table population
        import PySide6.QtCore as QtCore
        QtCore.QTimer.singleShot(50, lambda: self._finish_ui_population())

    def _finish_ui_population(self):
        self.apply_filter(self.cmb_filter.currentText())
        self.update_progress("Completado", 100)
        
    def apply_filter(self, status: str):
        self.table.setRowCount(0)
        filtered = self.all_results
        if status != "Todos":
            filtered = [r for r in self.all_results if r.status == status]
            
        self.table.setRowCount(len(filtered))
        
        stats = {"OK": 0, "FALTANTE": 0, "DIFERENTE": 0, "SOLO_NAS": 0}
        for r in self.all_results:
            stats[r.status] += 1
            
        for row, res in enumerate(filtered):
            item_status = QTableWidgetItem(res.status)
            if res.status == "FALTANTE": item_status.setForeground(Qt.red)
            elif res.status == "OK": item_status.setForeground(Qt.darkGreen)
            elif res.status == "DIFERENTE": item_status.setForeground(Qt.darkYellow) # El usuario pidió amarillo
            elif res.status == "SOLO_NAS": item_status.setForeground(Qt.blue)
            
            self.table.setItem(row, 0, item_status)
            self.table.setItem(row, 1, QTableWidgetItem(res.path))
            
            s_loc = str(res.size_local) if res.size_local is not None else "-"
            s_nas = str(res.size_nas) if res.size_nas is not None else "-"
            self.table.setItem(row, 2, QTableWidgetItem(s_loc))
            self.table.setItem(row, 3, QTableWidgetItem(s_nas))
            
            d_loc = res.mod_time_local.strftime("%Y-%m-%d %H:%M:%S") if res.mod_time_local else "-"
            d_nas = res.mod_time_nas.strftime("%Y-%m-%d %H:%M:%S") if res.mod_time_nas else "-"
            self.table.setItem(row, 4, QTableWidgetItem(d_loc))
            self.table.setItem(row, 5, QTableWidgetItem(d_nas))
            
        summary = f"Total procesados: {len(self.all_results)} | OK: {stats['OK']} | Faltantes: {stats['FALTANTE']} | Diferentes: {stats['DIFERENTE']} | Solo NAS: {stats['SOLO_NAS']}"
        self.lbl_summary.setText(summary)
        
    def comparison_error(self, error_msg: str):
        logging.error(f"Error en comparación: {error_msg}")
        self.btn_compare.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        QMessageBox.critical(self, "Error", f"Ocurrió un error: {error_msg}")
        
    def _get_current_results(self):
        status = self.cmb_filter.currentText()
        if status == "Todos":
            return self.all_results
        return [r for r in self.all_results if r.status == status]

    def export_csv(self):
        results = self._get_current_results()
        if not results: 
            QMessageBox.information(self, "Info", "No hay datos para exportar.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar a CSV", "", "CSV Files (*.csv)")
        if file_path:
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
            try:
                Exporter.export_to_csv(results, file_path)
                QMessageBox.information(self, "Éxito", "Exportado correctamente.")
                logging.info(f"Exportado CSV: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo exportar: {e}")
                
    def export_excel(self):
        results = self._get_current_results()
        if not results: 
            QMessageBox.information(self, "Info", "No hay datos para exportar.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar a Excel", "", "Excel Files (*.xlsx)")
        if file_path:
            if not file_path.lower().endswith('.xlsx'):
                file_path += '.xlsx'
            try:
                Exporter.export_to_excel(results, file_path)
                QMessageBox.information(self, "Éxito", "Exportado correctamente.")
                logging.info(f"Exportado Excel: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo exportar: {e}")

    def start_upload(self):
        missing_files = [r for r in self.all_results if r.status in ("FALTANTE", "DIFERENTE")]
        if not missing_files:
            QMessageBox.information(self, "Info", "No hay archivos faltantes o diferentes para subir.")
            return
            
        local_path = self.txt_local.text().strip()
        remote_path = self.txt_nas.text().strip()
        overwrite = self.cmb_overwrite.currentText()
        
        reply = QMessageBox.question(self, "Confirmar subida", 
                                     f"Se van a subir {len(missing_files)} archivos.\n\nDestino: {remote_path}\nSobrescribir: {overwrite}\n\n¿Continuar?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.btn_upload.setEnabled(False)
            self.btn_compare.setEnabled(False)
            
            self.upload_worker = UploaderWorker(self.synology_client, missing_files, local_path, remote_path, overwrite)
            self.upload_worker.progress.connect(self.update_progress)
            self.upload_worker.finished.connect(self.upload_finished)
            self.upload_worker.error.connect(self.comparison_error)
            self.upload_worker.start()

    def upload_finished(self, success: int, failed: int):
        self.btn_upload.setEnabled(True)
        self.btn_compare.setEnabled(True)
        self.progress_bar.setValue(100)
        
        msg = f"Subida completada.\n\nÉxito: {success}\nFallidos: {failed}"
        logging.info(msg.replace('\n', ' '))
        QMessageBox.information(self, "Subida Finalizada", msg)

