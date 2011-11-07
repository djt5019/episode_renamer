#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: qt.gui

import sys
import os
from PySide import QtGui, QtCore

from EpParser.src.Parser import EpParser
from EpParser.src.Cache import Cache
import EpParser.src.Utils as Utils

cache = Cache()
parser = EpParser(cache=cache)

class Window(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.form = Form()

        self.setCentralWidget( self.form )

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
        QtGui.QMessageBox.information(self,"Help Dialog", "Help Text")
                                
                
class Form(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        
        self.epLine = QtGui.QLineEdit()
        self.seasonBox = QtGui.QComboBox(self)
        self.findShowBtn = QtGui.QPushButton("&Find Show")
        self.epList = QtGui.QListWidget()
        self.fmtLine= QtGui.QLineEdit()
        
        self.seasonBox.addItem("All")		
        
        self.currentDirLine = QtGui.QLineEdit()		
        self.findDirBtn = QtGui.QPushButton("&Find Dir")			
        self.dirList = QtGui.QListWidget()
        self.renameBtn = QtGui.QPushButton("&Rename") 
        
        # Connect our signals
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
        vertLayout.addRow("&Search for show",self.epLine)	
        vertLayout.addRow("&Season",self.seasonBox)	
        vertLayout.addRow("&Episode Format", self.fmtLine)
        stackedWidget.setLayout(vertLayout)
        topLayout.addWidget(stackedWidget)
        topLayout.addWidget(self.epList)
        topLayout.addWidget(self.findShowBtn)
        leftWidget.setLayout(topLayout)
        
        label = QtGui.QLabel("Current Directory")
        self.currentDirLabel = QtGui.QLabel("<No Directory Selected>")
        label.setBuddy(self.currentDirLabel)
        #Set the right layout
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
        self.show = Utils.Show("")
        self.fmtLine.setText( self.show.formatter.formatString )
        self.renameDir = ""
        self.episodes = []
        self.formatter = Utils.EpisodeFormatter(self.show)
        
    def filterSeasons(self, text):
        self.episodes = self.show.episodeList
        if text == 'All':
            self.displayShow()
            return
            
        season = int(text)
        self.episodes = filter(lambda x: x.season==season, self.episodes)
        
        self.displayShow()
        
            
    def updateFormat(self):
        if self.fmtLine.text() != '':
            self.formatter.setFormat( self.fmtLine.text() )
            #Redisplay the episodes with the new format			
            self.displayShow()
        
        
    def findShow(self):
        showTitle = self.epLine.text().strip()
            
        if showTitle == "":
            InfoMessage(self, "Find Show", "No show specified")
            return        
        
        if self.show.title == showTitle:
            Utils.logger.debug("Searching for the same show as before, ignoring")
            return
        
        parser.setShow( showTitle )
        self.show = parser.getShow()
        self.formatter.show = self.show
        self.episodes = self.show.episodeList
        self.seasonBox.clear()
        self.seasonBox.addItem("All")
        if self.episodes != []:
            for s in xrange(self.episodes[-1].season):
                self.seasonBox.addItem( str(s+1) )
                
        self.displayShow()					          
            
    def displayShow(self):
        self.epList.clear()
        if self.episodes == []:
            InfoMessage(self, "Find Show", "Unable to find show, check spelling and try again")
            return
            
        for ep in self.episodes:
                self.epList.addItem( self.formatter.display(ep) )	
                
    def displayDirDialog(self):
        newDir = QtGui.QFileDialog.getExistingDirectory(self, 'Choose Directory', r'G:\TV\Misc')
        if newDir == '':
            return
            
        self.currentDirLabel.setText(os.path.abspath(newDir))
        self.renameDir = newDir
        self.dirList.clear()
        
        for f in Utils.cleanFilenames(self.renameDir):
            self.dirList.addItem( os.path.split(f)[1])
            
    def displayRenameDialog(self):
        if self.renameDir == "":
            InfoMessage(self, "Rename Files", "No Directory Selected")
            return
            
        
        if self.epList.count() == 0:
            InfoMessage(self, "Rename Files", "No Show Information Retrieved")
            return
            
        eps = [ self.formatter.display(x) for x in self.episodes ]
        files = Utils.renameFiles(self.renameDir, eps)
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
        self.fileList.addItem("-"*40)
        
        for old,new in self.files:
            try:
                old = Utils.encode(os.path.split(old)[1])
                new = Utils.encode(os.path.split(new)[1])
                string = Utils.encode("OLD: {}\nNEW:  {}\n".format(old, new))
            except:
                Utils.logger.critical( "Unable to rename " + new )
                
            self.fileList.addItem(string)
        
        self.show()
        
    def rename(self):
        errors = Utils.doRename(self.files, 'yes')
        self.fileList.clear()
        self.buttonBox.accepted.disconnect()
        
        if errors:
            self.fileList.addItem("&The following files could not be renamed\n")
            for e in errors:
                self.fileList.addItem(e)
                Utils.logger.error('Unable to rename: {}'.format(e) )
        else:
            self.fileList.addItem("The files were renamed successfully")
            Utils.logger.info("Filenames renamed succesfully")
            
        self.buttonBox.accepted.connect(self.close)
        self.buttonBox.rejected.connect(self.close)
            
        
def main():
    app = QtGui.QApplication("&My App")
    form = Window()
    form.show()
    
    ret =  app.exec_()
    form.close()
    
    return ret

if __name__ == '__main__':
    main()
