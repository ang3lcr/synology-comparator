import sys
import logging
from PySide6.QtWidgets import QApplication
from app.gui.main_window import MainWindow

def setup_logging():
    logging.basicConfig(
        filename='app.log',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        encoding='utf-8'
    )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

def main():
    setup_logging()
    logging.info("Iniciando Synology File Comparator")
    app = QApplication(sys.argv)
    
    # Modern style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
