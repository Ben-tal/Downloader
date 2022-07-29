import re
import sys
import urllib.request

import requests
import PySide6
from ui_popup import Ui_Dialog
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from ui_main import Ui_MainWindow


class PopUp(QWidget):
    def __init__(self, POPUP_SIGNAL):
        super(PopUp, self).__init__(parent=None)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.POPUP_SIGNAL = POPUP_SIGNAL

        self.setWindowTitle("PySide6")
        self.ui.pushButton.clicked.connect(self.close)

    def closeEvent(self, event):
        self.POPUP_SIGNAL.emit()
        super(PopUp, self).closeEvent(event)


class MainWindow(QMainWindow):
    PROGRESS_BAR_SIGNAL = Signal(int)
    ON_CLOSE_POPUP_SIGNAL = Signal()

    def __init__(self):
        super(MainWindow, self).__init__(parent=None)
        self.popup = PopUp(self.ON_CLOSE_POPUP_SIGNAL)
        self.ON_CLOSE_POPUP_SIGNAL.connect(lambda: self.setEnabled(True))
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Updater")
        self.ui.listWidget.clear()
        self.releases = {}
        self.ui.toolButton.clicked.connect(lambda: self.GetFile(self.ui.lineEdit))
        self.ui.toolButton_2.clicked.connect(lambda: self.GetDirectory(self.ui.lineEdit_2))
        self.ui.lineEdit_3.textChanged.connect(self.CheckValidURL)
        self.ui.listWidget.currentItemChanged.connect(self.ChangeList)
        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton_2.setEnabled(False)
        self.ui.pushButton_2.clicked.connect(self.Download)
        self.ui.pushButton.clicked.connect(self.start)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.PROGRESS_BAR_SIGNAL.connect(self.ui.progressBar.setValue)

    def ChangeList(self, selected_name, deselected_name):
        total = ""
        self.ui.tableWidget.clearMask()
        self.ui.tableWidget.setRowCount(0)
        for key, value in self.releases.get(selected_name.text()).items():
            total += f"{key}: {value}\r\n"
            if key == "assets":
                for asset in value:
                    currentRow = self.ui.tableWidget.rowCount()
                    self.ui.tableWidget.setRowCount(currentRow + 1)
                    self.ui.tableWidget.setItem(currentRow, 0, QTableWidgetItem(asset["name"]))
                    self.ui.tableWidget.setItem(currentRow, 1, QTableWidgetItem(asset["content_type"]))
                    self.ui.tableWidget.setItem(currentRow, 2, QTableWidgetItem(str(asset["size"])))
                    self.ui.tableWidget.setItem(currentRow, 3, QTableWidgetItem(str(asset["download_count"])))
                    self.ui.tableWidget.setItem(currentRow, 4, QTableWidgetItem(asset["updated_at"]))
                    self.ui.tableWidget.setItem(currentRow, 5, QTableWidgetItem(asset["created_at"]))
                    self.ui.tableWidget.setItem(currentRow, 6, QTableWidgetItem(asset["browser_download_url"]))
            elif key == "tarball_url" or key == "zipball_url":
                currentRow = self.ui.tableWidget.rowCount()
                self.ui.tableWidget.setRowCount(currentRow + 1)
                self.ui.tableWidget.setItem(currentRow, 0, QTableWidgetItem("SOURCE_CODE"))
                self.ui.tableWidget.setItem(currentRow, 1, QTableWidgetItem(key.replace("_url", "")))
                self.ui.tableWidget.setItem(currentRow, 2, QTableWidgetItem("NA"))
                self.ui.tableWidget.setItem(currentRow, 3, QTableWidgetItem("NA"))
                self.ui.tableWidget.setItem(currentRow, 4, QTableWidgetItem("NA"))
                self.ui.tableWidget.setItem(currentRow, 5, QTableWidgetItem("NA"))
                self.ui.tableWidget.setItem(currentRow, 6, QTableWidgetItem(value))
            elif key == "body":
                self.ui.textEdit.setText(value)
        self.ui.pushButton_2.setEnabled(True)

    def Download(self):
        self.ui.progressBar.clearMask()
        self.ui.tableWidget.currentRow()
        url = self.ui.tableWidget.item(self.ui.tableWidget.currentRow(), 6).text()
        name = self.ui.tableWidget.item(self.ui.tableWidget.currentRow(), 0).text()
        content_type = self.ui.tableWidget.item(self.ui.tableWidget.currentRow(), 1).text()
        if content_type == "zipball":
            name = name + ".zip"
        elif content_type == "tarball":
            name = name + ".tar.gz"
        # req = requests.get(self.url + "/" + self.ui.listWidget.currentItem().text())
        # if "message" in req.json().keys():
        #     text = f"Something went wrong, {req.json()['message']}"
        # elif "assets" not in req.json().keys():
        #     text = "Something went wrong, No assets found"
        # else:
        # url = req.json()["assets"][0].get("browser_download_url")
        # name = req.json()["assets"][0].get("name")
        print(f"[Starting Download] {url}")
        urllib.request.urlretrieve(url, name, self.UpdateProgressBar)
        print("[Download Complete]")
        text = "Download Complete"
        self.setEnabled(False)
        self.popup.ui.label.setText(text)
        self.popup.show()
        self.ui.progressBar.setValue(0)

    def UpdateInfo(self, url):
        req = requests.get(url)
        if "message" in req.json().keys():
            text = f"Something went wrong, {req.json()['message']}"
        elif "assets" not in req.json().keys():
            text = "Something went wrong, No assets found"
        else:
            for asset in req.json()["assets"]:
                url = asset.get("browser_download_url")
                name = asset.get("name")

    def UpdateProgressBar(self, block_num, block_size, total_size):
        if total_size == -1:
            return
        present = round(block_num * block_size * 100 / total_size)
        self.PROGRESS_BAR_SIGNAL.emit(present)

    def GetFile(self, lineEdit):
        lineEdit.setText(QFileDialog.getOpenFileName()[0])

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
        self.ui.progressBar.clearMask()
        self.ui.pushButton_2.setEnabled(False)
        if self.ui.comboBox.currentText() == "Github Release":
            print("GitHub Release")
            userGit, repoGit = self.ui.lineEdit_3.text().rsplit("/", 2)[1:3]
            self.url = f"https://api.github.com/repos/{userGit}/{repoGit}/releases"
            print(userGit, repoGit)
            current_req = requests.get(f"https://api.github.com/repos/{userGit}/{repoGit}/releases")
            releases = current_req.json()
            self.ui.listWidget.clear()
            for release in releases:
                tag_name = release.pop("tag_name")
                self.ui.listWidget.addItem(tag_name)
                self.releases.update({tag_name: release})
            print(self.releases)


if __name__ == "__main__":
    app = QApplication()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
