import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QComboBox, QProgressBar, QTextEdit, QCheckBox,
                            QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pcileecher import PCILeecher
from qconcursos_leecher import QConcursosLeecher
import logging

class DownloadWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, leecher, params):
        super().__init__()
        self.leecher = leecher
        self.params = params

    def run(self):
        try:
            if isinstance(self.leecher, PCILeecher):
                items = self.leecher.search_provas_e_gabaritos(
                    self.params['query'],
                    self.params.get('ano'),
                    self.params.get('banca'),
                    self.params.get('gabaritos', True)
                )
                
                total = 0
                for item in items:
                    try:
                        if self.leecher.download_item(item, self.params['pasta']):
                            total += 1
                            self.progress.emit(f"Baixado: {item['nome']}")
                    except Exception as e:
                        self.error.emit(str(e))
                
                self.finished.emit(total)
            
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCILeecher & QConcursos")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # Layout principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Seleção do site
        site_layout = QHBoxLayout()
        site_label = QLabel("Site:")
        self.site_combo = QComboBox()
        self.site_combo.addItems(["PCI Concursos", "QConcursos"])
        site_layout.addWidget(site_label)
        site_layout.addWidget(self.site_combo)
        layout.addLayout(site_layout)

        # Campos de busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite os termos de busca (ex: cesgranrio ti)")
        search_layout.addWidget(QLabel("Busca:"))
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Filtros
        filter_layout = QHBoxLayout()
        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("Ano (opcional)")
        self.banca_input = QLineEdit()
        self.banca_input.setPlaceholderText("Banca (opcional)")
        filter_layout.addWidget(QLabel("Ano:"))
        filter_layout.addWidget(self.year_input)
        filter_layout.addWidget(QLabel("Banca:"))
        filter_layout.addWidget(self.banca_input)
        layout.addLayout(filter_layout)

        # Opções
        options_layout = QHBoxLayout()
        self.gabaritos_check = QCheckBox("Baixar gabaritos")
        self.gabaritos_check.setChecked(True)
        options_layout.addWidget(self.gabaritos_check)
        layout.addLayout(options_layout)

        # Botões
        button_layout = QHBoxLayout()
        self.search_button = QPushButton("Buscar")
        self.search_button.clicked.connect(self.start_download)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # Progress Bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.worker = None

    def log(self, message):
        self.log_text.append(message)

    def start_download(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Erro", "Digite um termo de busca!")
            return

        # Prepara parâmetros
        params = {
            'query': query,
            'ano': self.year_input.text().strip() or None,
            'banca': self.banca_input.text().strip() or None,
            'gabaritos': self.gabaritos_check.isChecked(),
            'pasta': QFileDialog.getExistingDirectory(self, "Selecione a pasta para download")
        }

        if not params['pasta']:
            return

        # Cria worker apropriado
        if self.site_combo.currentText() == "PCI Concursos":
            leecher = PCILeecher()
        else:
            leecher = QConcursosLeecher()
            # Precisaria implementar login aqui

        self.worker = DownloadWorker(leecher, params)
        self.worker.progress.connect(self.log)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.download_finished)

        self.search_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setMaximum(0)
        self.worker.start()

    def cancel_download(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.log("Download cancelado!")
            self.search_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.progress_bar.setMaximum(100)

    def handle_error(self, error_msg):
        self.log(f"Erro: {error_msg}")

    def download_finished(self, total):
        self.log(f"\nDownload concluído! {total} arquivos baixados.")
        self.search_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
