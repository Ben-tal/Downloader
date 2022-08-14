import re
import sys
import threading
import urllib.request
import requests
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from ui_main import Ui_MainWindow

class MainWindow(QMainWindow):
    PROGRESS_BAR_SIGNAL = Signal(int)
    COMPLETED_SIGNAL = Signal()

    def __init__(self):
        super(MainWindow, self).__init__(parent=None)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Downloader")
        self.ui.listWidget.clear()
        self.releases = {}
        self.ui.toolButton_2.clicked.connect(lambda: self.GetDirectory(self.ui.lineEdit_2))
        self.ui.lineEdit_3.textChanged.connect(self.CheckValidURL)
        self.ui.listWidget.currentItemChanged.connect(self.ChangeList)
        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton_2.setEnabled(False)
        self.ui.pushButton_2.clicked.connect(self.Download)
        self.ui.pushButton.clicked.connect(self.start)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableWidget.currentItemChanged.connect(self.ChangeTable)
        self.PROGRESS_BAR_SIGNAL.connect(self.ui.progressBar.setValue)
        self.COMPLETED_SIGNAL.connect(self.Completed)

    def ChangeList(self, selected_name, deselected_name):
        self.ui.tableWidget.clearMask()
        self.ui.tableWidget.setRowCount(0)
        self.ui.pushButton_2.setEnabled(False)
        if not selected_name:
            return
        for key, value in self.releases.get(selected_name.tag_name).items():
            if key == "assets":
                for asset in value:
                    currentRow = self.ui.tableWidget.rowCount()
                    self.ui.tableWidget.setRowCount(currentRow + 1)
                    self.ui.tableWidget.setItem(currentRow, 0, QTableWidgetItem(asset["name"]))
                    self.ui.tableWidget.setItem(currentRow, 1, QTableWidgetItem(asset["content_type"]))
                    size = QTableWidgetItem()
                    size.setText(f"{asset['size']} bytes")
                    size.setData(Qt.UserRole+1, int(asset["size"]))
                    self.ui.tableWidget.setItem(currentRow, 2, size)
                    self.ui.tableWidget.setItem(currentRow, 3, QTableWidgetItem(str(asset["download_count"])))
                    self.ui.tableWidget.setItem(currentRow, 4, QTableWidgetItem(asset["updated_at"]))
                    self.ui.tableWidget.setItem(currentRow, 5, QTableWidgetItem(asset["created_at"]))
                    self.ui.tableWidget.setItem(currentRow, 6, QTableWidgetItem(asset["browser_download_url"]))
            elif key == "tarball_url" or key == "zipball_url":
                currentRow = self.ui.tableWidget.rowCount()
                self.ui.tableWidget.setRowCount(currentRow + 1)
                self.ui.tableWidget.setItem(currentRow, 0, QTableWidgetItem("SOURCE_CODE"))
                self.ui.tableWidget.setItem(currentRow, 1, QTableWidgetItem(key.replace("_url", "")))
                size = QTableWidgetItem()
                size.setText("NA")
                size.setData(Qt.UserRole + 1, 0)
                self.ui.tableWidget.setItem(currentRow, 2, size)
                self.ui.tableWidget.setItem(currentRow, 3, QTableWidgetItem("NA"))
                self.ui.tableWidget.setItem(currentRow, 4, QTableWidgetItem("NA"))
                self.ui.tableWidget.setItem(currentRow, 5, QTableWidgetItem("NA"))
                self.ui.tableWidget.setItem(currentRow, 6, QTableWidgetItem(value))
            elif key == "body":
                self.ui.textEdit.setText(value)

    def ChangeTable(self):
        self.ui.pushButton_2.setEnabled(True)

    def Download(self):
        self.ui.tableWidget.currentRow()
        url = self.ui.tableWidget.item(self.ui.tableWidget.currentRow(), 6).text()
        name = self.ui.tableWidget.item(self.ui.tableWidget.currentRow(), 0).text()
        content_type = self.ui.tableWidget.item(self.ui.tableWidget.currentRow(), 1).text()
        if content_type == "zipball":
            name = name + ".zip"
        elif content_type == "tarball":
            name = name + ".tar.gz"
        if not self.ui.lineEdit_2.text():
            QMessageBox.warning(self, "Warning", "Please select a directory")
            return
        print(f"[Starting Download]\r\n{url}")
        d_thread = threading.Thread(target=self.DownloadThread, args=(url, name))
        d_thread.start()

    def Completed(self):
        QMessageBox.information(self, "Information", "Download Complete")
        self.ui.progressBar.setValue(0)

    def DownloadThread(self, url, name):
        urllib.request.urlretrieve(url, f"{self.ui.lineEdit_2.text()}/{name}", self.UpdateProgressBar)
        print("[Download Complete]")
        self.COMPLETED_SIGNAL.emit()

    def UpdateProgressBar(self, block_num, block_size, total_size):
        if total_size == -1:
            return
        present = round(block_num * block_size * 100 / total_size)
        self.PROGRESS_BAR_SIGNAL.emit(present)

    def GetDirectory(self, lineEdit):
        lineEdit.setText(QFileDialog.getExistingDirectory())

    def CheckValidURL(self, url):
        if re.match(
                r"^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$",
                url):
            self.ui.pushButton.setEnabled(True)
        else:
            self.ui.pushButton.setEnabled(False)

    def start(self):
        self.ui.pushButton_2.setEnabled(False)
        if self.ui.comboBox.currentText() == "Github Release":
            if self.ui.lineEdit_3.text()[-1] == "/":
                self.ui.lineEdit_3.setText(self.ui.lineEdit_3.text()[:-1])
            userGit, repoGit = self.ui.lineEdit_3.text().rsplit("/", 2)[1:3]
            current_req = requests.get(f"https://api.github.com/repos/{userGit}/{repoGit}/releases")
            releases = current_req.json()
            self.ui.listWidget.clear()
            if type(releases) is dict and "message" in releases.keys():
                QMessageBox.warning(self, "Warning", releases["message"])
                return
            for release in releases:
                tag_name = release.pop("tag_name")
                preview = release.pop("prerelease")
                draft = release.pop("draft")
                display = tag_name
                if preview:
                    display += " (Preview)"
                if draft:
                    display += " (Draft)"
                _ = QListWidgetItem(display)
                _.tag_name = tag_name
                self.ui.listWidget.addItem(_)
                self.releases.update({tag_name: release})


if __name__ == "__main__":
    app = QApplication()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
