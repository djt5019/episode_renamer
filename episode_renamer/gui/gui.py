# -*- coding: utf-8 -*-
#!/usr/bin/env python
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import os
import logging

from PySide import QtGui, QtCore

from episode_renamer.Parser import Parser
from episode_renamer.Episode import Show, EpisodeFormatter
from episode_renamer.Cache import Cache

from episode_renamer import Utils

cache = Cache()
parser = Parser(cache=cache)
Utils.load_renamed_file()

## Snuff the console output for the gui
log = logging.getLogger()
for handler in log.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setLevel(logging.CRITICAL)
        del log
        break


class UpdateDisplaySignal(QtCore.QObject):
    update_directory = QtCore.Signal()
    update_episodes = QtCore.Signal()


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

        # Prepare the display update signals
        self.updater = UpdateDisplaySignal()
        self.updater.update_directory.connect(self.updateDirectoryListing)
        self.updater.update_episodes.connect(self.updateEpisodeListing)

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
        self.renameDir = ""
        self.episodes = []
        self.formatter = EpisodeFormatter(self.show)
        self.show.formatter = self.formatter
        self.fmtLine.setText(self.show.formatter.format_string)
        print "Loaded Config"

    def updateDirectoryListing(self):
        self.dirList.clear()
        for ep in Utils.clean_filenames(self.renameDir):
            self.dirList.addItem(ep.name)

    def updateEpisodeListing(self):
        if not self.episodes:
            InfoMessage(self, "Find Show", "Unable to find show, check spelling and try again")
            return

        self.epList.clear()
        for ep in self.episodes:
            self.epList.addItem(self.show.formatter.display(ep))

    def filterSeasons(self, text):
        if text == 'All':
            self.updater.update_episodes.emit()
            return

        season = int(text)
        self.episodes = self.show.get_season(season)

        self.updater.update_episodes.emit()

    def updateFormat(self):
        if self.fmtLine.text() != '':
            self.formatter.format_string = self.fmtLine.text()

        if self.show.title != "":
            self.updater.update_episodes.emit()

    def findShow(self):
        showTitle = Utils.remove_punctuation(self.epLine.text().strip())

        if not showTitle:
            InfoMessage(self, "Find Show", "No show specified")
            return

        parser.setShow(showTitle)
        self.show = parser.getShow()
        self.formatter.show = self.show
        self.show.formatter = self.formatter
        self.episodes = self.show.episodes
        self.seasonBox.clear()
        self.seasonBox.addItem("All")
        if self.episodes:
            for s in xrange(self.show.num_seasons):
                self.seasonBox.addItem(str(s + 1))

        self.updater.update_episodes.emit()

    def displayDirDialog(self):
        newDir = QtGui.QFileDialog.getExistingDirectory(self, 'Choose Directory', r'G:\TV\Misc')
        if newDir == '':
            return

        self.currentDirLabel.setText(os.path.abspath(newDir))
        self.renameDir = newDir
        self.dirList.clear()
        self.epLine.setText(os.path.split(self.renameDir)[1])

        self.updater.update_directory.emit()

    def displayRenameDialog(self):
        if self.renameDir == "":
            InfoMessage(self, "Rename Files", "No Directory Selected")
            return

        if self.epList.count() == 0:
            InfoMessage(self, "Rename Files", "No Show Information Retrieved")
            return

        files = Utils.prepare_filenames(self.renameDir, self.show)
        dialog = RenameDialog(files, self)
        dialog.finished.connect(self.updateDirectoryListing)
        dialog.exec_()

        self.updater.update_directory.emit()


class InfoMessage(object):
    def __init__(self, parent, windowTitle, msg):
        QtGui.QMessageBox.information(parent, windowTitle, msg)


class RenameDialog(QtGui.QDialog, object):
    def __init__(self, files, parent=None):
        super(RenameDialog, self).__init__(parent)
        self.setGeometry(100, 100, 750, 500)
        self.setWindowTitle("Rename Files Utility")

        self.files = files

        self.buttonBox = QtGui.QDialogButtonBox(QtCore.Qt.Vertical)
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.rename)
        self.buttonBox.rejected.connect(self.close)

        self.model = QtGui.QStandardItemModel()
        self.view = QtGui.QListView()

        self.view.setModel(self.model)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

        if not self.files:
            self.model.appendRow(QtGui.QStandardItem("No files need to be renamed"))
            self.view.show()
            self.show()
            return

        for old, new in self.files:
            item = QtGui.QStandardItem()

            try:
                old_name = Utils.encode(os.path.split(old)[1])
                new_name = Utils.encode(os.path.split(new)[1])
                string = Utils.encode("OLD: {}\nNEW: {}\n".format(old_name, new_name))
                item.setText(string)
                item.setCheckState(QtCore.Qt.Checked)
                item.setCheckable(True)
                item.rename_info = (old, new)
            except OSError:
                logging.critical("Unable to rename " + new)

            if item.text():
                self.model.appendRow(item)

        self.view.show()

    def rename(self):
        files = []

        for itemIndex in xrange(self.model.rowCount()):
            item = self.model.item(itemIndex)
            if item.checkState() == QtCore.Qt.Checked:
                files.append(item.rename_info)

        errors = Utils.rename(files, 'yes')
        self.model.clear()
        self.buttonBox.accepted.disconnect()

        if errors:
            self.model.appendRow(QtGui.QStandardItem("&The following files could not be renamed\n"))
            for e in errors:
                self.model.appendRow(QtGui.QStandardItem(e[0]))
                logging.error('Unable to rename: {}'.format(e))
        else:
            self.model.appendRow(QtGui.QStandardItem("The files were renamed successfully"))
            logging.info("Filenames renamed succesfully")

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
