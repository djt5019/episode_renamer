# -*- coding: utf-8 -*-
#!/usr/bin/env python
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import os
from PySide import QtGui, QtCore

from EpParser.src.Parser import EpParser
from EpParser.src.Episode import Show, EpisodeFormatter
from EpParser.src.Cache import Cache
from EpParser.src.Logger import get_logger
import EpParser.src.Utils as Utils

cache = Cache()
parser = EpParser(cache=cache)
logger = get_logger()


class Window(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.form = Form()

        self.setCentralWidget(self.form)

        exitAction = QtGui.QAction('&Exit', self)
        exitAction.setShortcut("&Ctrl+Q")
        exitAction.setStatusTip("&Exit the application")
        exitAction.triggered.connect(self.close)

        helpAction = QtGui.QAction('&Info', self)
        helpAction.setShortcut('F1')
        helpAction.setStatusTip("Show help menu")
        helpAction.triggered.connect(self.printHelp)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        helpMenu = menubar.addMenu('&Help')

        fileMenu.addAction(exitAction)
        helpMenu.addAction(helpAction)

        self.setWindowTitle('Menubar')

    def printHelp(self):
        QtGui.QMessageBox.information(self, "Help Dialog", "Help Text")


class Form(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)

        self.epLine = QtGui.QLineEdit()
        self.seasonBox = QtGui.QComboBox(self)
        self.findShowBtn = QtGui.QPushButton("&Find Show")
        self.epList = QtGui.QListWidget()
        self.fmtLine = QtGui.QLineEdit()

        self.seasonBox.addItem("All")

        self.currentDirLine = QtGui.QLineEdit()
        self.findDirBtn = QtGui.QPushButton("&Find Dir")
        self.dirList = QtGui.QListWidget()
        self.renameBtn = QtGui.QPushButton("&Rename")

        # Connect our signals
        self.epLine.returnPressed.connect(self.findShow)
        self.findDirBtn.clicked.connect(self.displayDirDialog)
        self.findShowBtn.clicked.connect(self.findShow)
        self.renameBtn.clicked.connect(self.displayRenameDialog)
        self.fmtLine.editingFinished.connect(self.updateFormat)
        self.seasonBox.activated[str].connect(self.filterSeasons)

        #Set the left layout
        leftWidget = QtGui.QWidget()
        stackedWidget = QtGui.QWidget()
        topLayout = QtGui.QVBoxLayout()
        vertLayout = QtGui.QFormLayout()
        vertLayout.addRow("&Search for show", self.epLine)
        vertLayout.addRow("&Season", self.seasonBox)
        vertLayout.addRow("&Episode Format", self.fmtLine)
        stackedWidget.setLayout(vertLayout)
        topLayout.addWidget(stackedWidget)
        topLayout.addWidget(self.epList)
        topLayout.addWidget(self.findShowBtn)
        leftWidget.setLayout(topLayout)

        #Set the right layout
        label = QtGui.QLabel("Current Directory")
        self.currentDirLabel = QtGui.QLabel("<No Directory Selected>")
        label.setBuddy(self.currentDirLabel)
        rightWidget = QtGui.QWidget()
        rightLayout = QtGui.QVBoxLayout()
        rightLayout.addWidget(label)
        rightLayout.addWidget(self.currentDirLabel)
        rightLayout.addWidget(self.findDirBtn)
        rightLayout.addWidget(self.dirList)
        rightLayout.addWidget(self.renameBtn)
        rightWidget.setLayout(rightLayout)

        #Connect the left widget and right widget
        displayBox = QtGui.QHBoxLayout()
        displayBox.addWidget(leftWidget)
        displayBox.addWidget(rightWidget)

        self.setLayout(displayBox)
        self.show = Show("")
        self.fmtLine.setText(self.show.formatter.formatString)
        self.renameDir = ""
        self.episodes = []
        self.formatter = EpisodeFormatter(self.show)
        self.formatter.load_format_config()

    def filterSeasons(self, text):
        if text == 'All':
            self.displayShow()
            return

        season = int(text)
        self.episodes = self.show.get_season(season)

        self.displayShow()

    def updateFormat(self):
        if self.fmtLine.text() != '':
            self.formatter.set_format(self.fmtLine.text())

        if self.show.title != "":
            self.displayShow()

    def findShow(self):
        showTitle = self.epLine.text().strip()

        if showTitle == "":
            InfoMessage(self, "Find Show", "No show specified")
            return

        parser.setShow(showTitle)
        self.show = parser.getShow()
        self.formatter.show = self.show
        self.show.formatter = self.formatter
        self.episodes = self.show.episodeList
        self.seasonBox.clear()
        self.seasonBox.addItem("All")
        if self.episodes != []:
            for s in xrange(self.show.numSeasons):
                self.seasonBox.addItem(str(s + 1))

        self.displayShow()

    def displayShow(self):
        if self.episodes == []:
            InfoMessage(self, "Find Show", "Unable to find show, check spelling and try again")
            return

        self.epList.clear()
        for ep in self.episodes:
            self.epList.addItem(self.show.formatter.display(ep))

    def displayDirDialog(self):
        newDir = QtGui.QFileDialog.getExistingDirectory(self, 'Choose Directory', r'G:\TV\Misc')
        if newDir == '':
            return

        self.currentDirLabel.setText(os.path.abspath(newDir))
        self.renameDir = newDir
        self.dirList.clear()

        for f in Utils.clean_filenames(self.renameDir):
            self.dirList.addItem(f.name)

    def displayRenameDialog(self):
        if self.renameDir == "":
            InfoMessage(self, "Rename Files", "No Directory Selected")
            return

        if self.epList.count() == 0:
            InfoMessage(self, "Rename Files", "No Show Information Retrieved")
            return

        files = Utils.prepare_filenames(self.renameDir, self.show)
        RenameDialog(files, self)


class InfoMessage(object):
    def __init__(self, parent, windowTitle, msg):
        QtGui.QMessageBox.information(parent, windowTitle, msg)


class RenameDialog(QtGui.QDialog):
    def __init__(self, files, parent=None):
        super(RenameDialog, self).__init__(parent)
        self.setGeometry(100, 100, 750, 500)
        self.setWindowTitle("&Rename Files Utility")

        self.files = files

        self.buttonBox = QtGui.QDialogButtonBox(QtCore.Qt.Vertical)
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.rename)
        self.buttonBox.rejected.connect(self.close)

        self.fileList = QtGui.QListWidget()

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.fileList)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

        self.fileList.addItem("Files will be renamed in the following format")
        self.fileList.addItem("-" * 55)

        if not self.files:
            self.fileList.addItem("No files need to be renamed")
            self.show()
            return

        for old, new in self.files:
            try:
                old = Utils.encode(os.path.split(old)[1])
                new = Utils.encode(os.path.split(new)[1])
                string = Utils.encode("OLD: {}\nNEW:  {}\n".format(old, new))
            except:
                logger.critical("Unable to rename " + new)

            self.fileList.addItem(string)

        self.show()

    def rename(self):
        errors = Utils.rename(self.files, 'yes')
        self.fileList.clear()
        self.buttonBox.accepted.disconnect()

        if errors:
            self.fileList.addItem("&The following files could not be renamed\n")
            for e in errors:
                self.fileList.addItem(e)
                logger.error('Unable to rename: {}'.format(e))
        else:
            self.fileList.addItem("The files were renamed successfully")
            logger.info("Filenames renamed succesfully")

        self.buttonBox.accepted.connect(self.close)
        self.buttonBox.rejected.connect(self.close)


def main():
    app = QtGui.QApplication("&My App")
    form = Window()
    form.show()

    ret = app.exec_()
    form.close()

    return ret

if __name__ == '__main__':
    main()
