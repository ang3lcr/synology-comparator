from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QMessageBox)
from app.synology.client import SynologyClient

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Conexión a Synology NAS")
        self.client = SynologyClient()
        self.connected = False
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Host / QuickConnect
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("QuickConnect ID / Host:"))
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Ej: MiNAS o 192.168.1.100")
        host_layout.addWidget(self.host_input)
        layout.addLayout(host_layout)
        
        # User
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Usuario:"))
        self.user_input = QLineEdit()
        user_layout.addWidget(self.user_input)
        layout.addLayout(user_layout)
        
        # Password
        pass_layout = QHBoxLayout()
        pass_layout.addWidget(QLabel("Contraseña:"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        pass_layout.addWidget(self.pass_input)
        layout.addLayout(pass_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_connect = QPushButton("Probar y Conectar")
        self.btn_connect.clicked.connect(self.try_connect)
        btn_layout.addWidget(self.btn_connect)
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_layout)
        
    def try_connect(self):
        host = self.host_input.text().strip()
        user = self.user_input.text().strip()
        password = self.pass_input.text()
        
        if not host or not user or not password:
            QMessageBox.warning(self, "Error", "Por favor llena todos los campos.")
            return
            
        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("Conectando...")
        
        try:
            # Basic connection using synology-api
            self.client.connect(host, user, password)
            self.connected = True
            QMessageBox.information(self, "Éxito", "Conectado correctamente al NAS.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error de Conexión", f"No se pudo conectar: {str(e)}")
            self.btn_connect.setEnabled(True)
            self.btn_connect.setText("Probar y Conectar")
