import sys
import os
import io
import logging
from PySide6.QtWidgets import QApplication
from app.gui.main_window import MainWindow

class SafeStream:
    def __init__(self, logger_func=None):
        self.logger_func = logger_func
        self.encoding = 'utf-8'
        self.errors = 'replace'
        self.closed = False

    def write(self, message):
        if not message:
            return 0
        text = str(message).rstrip('\r\n')
        if text and self.logger_func:
            self.logger_func(text)
        return len(str(message))

    def flush(self):
        pass

    def isatty(self):
        return False

    def readable(self):
        return False

    def writable(self):
        return True

    def seekable(self):
        return False

def setup_logging():
    log_file = 'app.log'
    if getattr(sys, 'frozen', False):
        log_file = os.path.join(os.path.dirname(sys.executable), 'app.log')
        
    try:
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
    except Exception:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    # In windowed mode (GUI), sys.stdout and sys.stderr are None.
    # We provide safe stream wrappers so libraries like tqdm and print do not crash.
    if sys.stdout is None or not hasattr(sys.stdout, 'write'):
        sys.stdout = SafeStream(logging.debug)
    else:
        try:
            logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        except Exception:
            pass

    if sys.stderr is None or not hasattr(sys.stderr, 'write'):
        sys.stderr = SafeStream(logging.warning)

    if sys.stdin is None:
        sys.stdin = io.StringIO()

def main():
    setup_logging()
    logging.info("Iniciando AD ASTRA")
    app = QApplication(sys.argv)
    app.setApplicationName("AD ASTRA")
    
    # Modern style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
