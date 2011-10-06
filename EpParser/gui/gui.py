#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author:  Dan Tracy
# program: qt.gui

import sys
from PySide import QtGui

import EpParser.src.Parser as Parser

class Window(QtGui.QMainWindow):
        def __init__(self, parent=None):
            super(Window, self).__init__(parent)
            self.form = Form()

            self.setCentralWidget( self.form )

            exitAction = QtGui.QAction('&Exit', self)
            exitAction.setShortcut("Ctrl+Q")
            exitAction.setStatusTip("Exit the application")
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
            dialog = QtGui.QMessageBox()            
            dialog.setText("Sweet Dialog Bro")
            dialog.setWindowTitle("Woah help dialog")
            dialog.show()
            dialog._exec()
                
                
                
class Form(QtGui.QWidget):
        def __init__(self, parent=None):
            super(Form, self).__init__(parent)
            self.setWindowTitle("Excellent Form Example")
            
            self.edit = QtGui.QLineEdit("Choose a TV Show: ")
            self.btn  = QtGui.QPushButton("FIND IT")
            self.list = QtGui.QListWidget()
            self.lst2 = QtGui.QListWidget()
            
            self.btn.clicked.connect(self.displayShows)
            self.edit.editingFinished.connect(self.changed)
            
            leftWidget = QtGui.QWidget()
            layout = QtGui.QVBoxLayout()
            layout.addWidget(self.edit)
            layout.addWidget(self.btn)
            layout.addWidget(self.list)
            leftWidget.setLayout(layout)
            
            leftBox = QtGui.QHBoxLayout()
            leftBox.addWidget(leftWidget)
            leftBox.addWidget(self.lst2)
            self.setLayout(leftBox)

            self.parser = Parser.EpParser()
                
        def displayShows(self):
            showTitle = self.edit.text().split(':',1)[1].strip()
            self.list.clear()
            
            if showTitle != '':
                self.parser.setShow( showTitle )
                show = self.parser.parseData()
                for ep in show.episodeList:
                    self.list.addItem( show.formatter.display(ep) )
                            
            self.edit.clear()
            self.edit.setText('Choose a TV Show: ')
            
        def changed(self):
                print "The text has been changed"                
                
                
                
def main():
    app = QtGui.QApplication("My App")
    form = Window()
    form.show()
    
    ret =  app.exec_()
    form.close()
    
    return ret

if __name__ == '__main__':
    main()
