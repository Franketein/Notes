#!/usr/bin/env python3

import sys
import os
import urllib.request
from PyQt5 import QtWidgets, QtGui, QtCore
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import argparse

mainpath = os.path.dirname(os.path.realpath(__file__)) + '/'

def parseArguments():
    parser = argparse.ArgumentParser(description='Manage and backup your notes')

    parser.add_argument('-n', '--new', action='store_const', const='trueNew', help='create a new note')

    args = parser.parse_args()
    return args

def internet_on():
    for timeout in [1, 5]:
        try:
            response=urllib.request.urlopen('http://google.com',timeout=timeout)
            return True
        except urllib.request.URLError as err: pass
    return False

class SpreadSheet():
    if internet_on():
        scope = ['https://spreadsheets.google.com/feeds']
        creds = ServiceAccountCredentials.from_json_keyfile_name(mainpath + 'client_secret.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open('Notes').sheet1

        def __init__(self):
            self.title = ""
            self.text = ""
            self.progress = 0


        def loadNote(self, row):
            self.title = SpreadSheet.sheet.cell(row, 1).value
            self.text = SpreadSheet.sheet.cell(row, 2).value

        def saveNote(self, row, title, text, date):
            formatedDate = date.toString()
            try:
                if row == '':
                    cell = SpreadSheet.sheet.find(title)
                    row = cell.row

                SpreadSheet.sheet.update_cell(row, 1, title)
                SpreadSheet.sheet.update_cell(row, 2, text)
                SpreadSheet.sheet.update_cell(row, 3, formatedDate)
            except:
                values = [title, text, formatedDate]
                SpreadSheet.sheet.append_row(values)
                # SpreadSheet.sheet.update_cell(row, 1, title)
                # SpreadSheet.sheet.update_cell(row, 2, text)
                # SpreadSheet.sheet.update_cell(row, 3, date)

        # def loadRecents(self):
        #     self.progress = 0
        #     return SpreadSheet.sheet.range('F2:G6')
        #
        # def changeRecents(self, caller, path, name):
        #     for col in range(6, 8):
        #         for i in range(6, 2, -1):
        #             SpreadSheet.sheet.update_cell(i, col, SpreadSheet.sheet.cell(i-1, col).value)
        #             caller.loadProgress.setValue(self.progress)
        #             self.progress += 15
        #
        #     SpreadSheet.sheet.update_cell(2, 6, name)
        #     SpreadSheet.sheet.update_cell(2, 7, path)

class ExplorerSystemModel(QtWidgets.QFileSystemModel):

    def columnCount(self, parent=QtCore.QModelIndex()):
        return super(ExplorerSystemModel, self).columnCount()

    def data(self, index, role):
        if index.column() == 2:
            if role == QtCore.Qt.BackgroundColorRole:
                return QtCore.Qt.cyan

        return super(ExplorerSystemModel, self).data(index, role)

    def headerData(self, index, Qt_Orientation, role):

        if index == 2:
            if role == QtCore.Qt.DisplayRole:
                return "Label"
        else:
            if role == QtCore.Qt.DisplayRole:
                return QtWidgets.QFileSystemModel().headerData(index, Qt_Orientation, role)

class Window(QtWidgets.QMainWindow):
    # if internet_on() == True:
    #     worksheet = SpreadSheet()
    # else:
    #     worksheet = None

    def __init__(self):
        if internet_on():
            self.worksheet = SpreadSheet()
        else:
            self.worksheet = None

        self.title = "My Notes"
        self.text = ""

        self.notSynced = []

        self.lastToolbar = ""
        self.editorOpened = False

        super(Window, self).__init__()
        self.resize(450, 500)

        self.setWindowIcon(QtGui.QIcon(mainpath + 'icon.png'))

        self.mainMenu = self.menuBar()
        self.fileMenu = self.mainMenu.addMenu('File')
        self.editorMenu = self.mainMenu.addMenu('Editor')

        self.menuAction("New Note", "Ctrl+N", self.new, self.fileMenu)
        # self.menuAction("Open Note", "Ctrl+O", self.open, self.fileMenu)
        self.saveActionMenu = self.menuAction("Save Note", "Ctrl+S", self.save, self.fileMenu)
        self.menuAction("Minimize", "Ctrl+M", self.showMinimized, self.fileMenu)
        self.menuAction("Exit", "Ctrl+Q", self.close, self.fileMenu)

        self.menuAction("Font", "", sys.exit, self.editorMenu)
        self.editorAction = self.menuAction("Close Editor", "Ctrl+E", self.openHome, self.editorMenu)

        self.toolBar = self.addToolBar("editorToolbar")

        # self.toolbarAction("openNote.png", "Open Note", self.open, "Open")
        self.toolbarAction(mainpath + "newNote.png", "New Note", self.new)
        self.saveActionToolbar = self.toolbarAction(mainpath + "saveNote.png", "Save Note", self.save)

        self.titleInput = self.toolBar.addWidget(QtWidgets.QLineEdit()).defaultWidget()

        self.editor = QtWidgets.QPlainTextEdit()
        self.home = QtWidgets.QWidget()

        self.pageManager = QtWidgets.QStackedWidget()

        vbox = QtWidgets.QVBoxLayout()
        rf = QtWidgets.QLabel()
        rf.setText("Recent Files:")

        self.rfList = QtWidgets.QListWidget()

        self.openHome()

        self.pageManager.setMouseTracking(True)

        self.home.setLayout(vbox)
        vbox.addWidget(rf)
        # vbox.addWidget(self.rfList)
        self.fileTree = self.fileView()
        self.defaultEvent = self.fileTree.mouseDoubleClickEvent
        self.fileTree.mouseDoubleClickEvent = self.myDoubleClickEvent


        vbox.addWidget(self.fileTree)

        self.statusBar()

        self.loadProgress = QtWidgets.QProgressBar()

        self.pageManager.addWidget(self.home)
        self.pageManager.addWidget(self.editor)
        self.pageManager.addWidget(self.loadProgress)
        self.setCentralWidget(self.pageManager)

        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon(mainpath + 'icon.png'))

        show_action = QtWidgets.QAction("Show", self)
        quit_action = QtWidgets.QAction("Exit", self)
        hide_action = QtWidgets.QAction("Hide", self)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(self.exit)
        tray_menu = QtWidgets.QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.show()

        args = str(parseArguments())
        if "trueNew" in args:
            self.new()
            self.express = True
        else:

            self.express = False

    def myDoubleClickEvent(self, event):
        if event.button() == 1:
            self.defaultEvent(event)

    def openHome(self):

        if self.editorOpened:
            choice = QtWidgets.QMessageBox.question(self, "Are You Sure?",
                                                    "You have an open note, are you sure you want "
                                                    "to close it",
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.No:
                return

        self.pageManager.setCurrentIndex(0)

        self.title = "My Notes"
        self.text = ""
        self.titleInput.setText('')
        self.setWindowTitle(self.title)

        self.editor.setPlainText(self.text)

        self.editorOpened = False

        self.editorAction.setEnabled(False)
        self.saveActionMenu.setEnabled(False)
        self.saveActionToolbar.setEnabled(False)

        self.titleInput.setEnabled(False)

        # self.rfList.clear()
        # recentsRange = self.worksheet.loadRecents()
        # for i,cell in enumerate(recentsRange):
        #     if cell.value != "":
        #         if i == 0 or i%2 == 0:
        #             link = QtWidgets.QPushButton()
        #
        #             link.clicked.connect(self.openFile)
        #
        #             link.setText(cell.value)
        #
        #             link.setFlat(True)
        #             link.setStyleSheet('color: blue; text-decoration: underline; text-align: left;')
        #
        #             cursor = QtGui.QCursor()
        #             cursor.setShape(13)
        #
        #             link.setCursor(cursor)
        #
        #         else:
        #             if cell.value != "":
        #                 self.rfList.addItem("")
        #
        #                 link.setToolTip(cell.value)
        #                 link.setStatusTip(cell.value)
        #
        #                 self.rfList.setItemWidget(self.rfList.item(i - i/2 - i%2 + 0.5), link)

    def fileView(self):
        model = QtWidgets.QFileSystemModel()
        model.setRootPath(mainpath + "notes/")

        view = QtWidgets.QTreeView()
        view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        view.customContextMenuRequested.connect(self.openPopup)
        view.doubleClicked.connect(self.openFile)

        view.setModel(model)


        view.hideColumn(1)
        view.hideColumn(2)
        view.sortByColumn(3, 1)
        view.setColumnWidth(0, 190)
        view.setColumnWidth(1, 70)

        view.setRootIndex(model.index(mainpath + "notes/"))

        return view

    def openPopup(self, position):
        menu = QtWidgets.QMenu()
        delete = menu.addAction("Delete")
        delete.triggered.connect(self.delete)
        menu.exec(self.fileTree.viewport().mapToGlobal(position))

    def closeEvent(self, event):
        if self.express == False:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Tray Program",
                "Application was minimized to Tray",
                QtWidgets.QSystemTrayIcon.Information,
                2000
            )

    def delete(self):
        selected = self.fileTree.selectedIndexes()
        for item in selected:
            if item.column() == 0:
                choice = QtWidgets.QMessageBox.question(self, "Are You Sure?",
                                                        "Are you sure you want to delete: \"" + item.data(0) +
                                                        "\"\nonce you click 'Yes' there's no way to recover it",
                                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if choice == QtWidgets.QMessageBox.No:
                    return

                path = mainpath + 'notes/' + item.data(0)
                os.remove(path)

    def new(self):
        if self.editorOpened == True:
            choice = QtWidgets.QMessageBox.question(self, "Are You Sure?",
                                                    "You have an open note, are you sure you want "
                                                    "to close it and create a new note",
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.No:
                return
        i = 1
        while True:
            if not os.path.isfile(mainpath + "notes/New Note" + str(i)):
                self.title = "New Note" + str(i)
                break
            i+=1
        self.text = ''
        self.titleInput.setText(self.title)
        self.openEditor()


    def openFile(self, filename):
        if (QtCore.Qt.LeftButton):
            # if filename.data(0)[len(filename.data(0))-1] != 'e':
            #     print(filename.data(32))
            # else:
            name = mainpath + "notes/" + filename.data(0)

            try:
                file = open(name, 'r')

                with file:
                    self.title = QtCore.QFileInfo(name).baseName()
                    self.titleInput.setText(self.title)
                    self.text = file.read()

                self.openEditor()
            # except UnicodeError:
            #     QtWidgets.QMessageBox.question(self, 'File type not compatible',
            #                                    "Could not open file type\n"
            #                                    "My Notes can only open text files like '.txt', '.py', etc.",
            #                                    QtWidgets.QMessageBox.Ok)
            except FileNotFoundError:
                QtWidgets.QMessageBox.question(self, 'File not found',
                                           "Could not find the file\n"
                                           "Check if the file still exists and the path to it hasn't changed",
                                           QtWidgets.QMessageBox.Ok)
            except:
                QtWidgets.QMessageBox.question(self, "Couldn't open file",
                                               "Could not open the note\n"
                                               "Check if the file still exists and the path to it hasn't changed\nor if it is the correct type",
                                               QtWidgets.QMessageBox.Ok)
        else:
            print("no left")
    # def open(self):
    #     if self.editorOpened == True:
    #         choice = QtWidgets.QMessageBox.question(self, "Are You Sure?",
    #                                                 "You have an open note, are you sure you want "
    #                                                 "to close it and open a different note",
    #                                                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    #         if choice == QtWidgets.QMessageBox.No:
    #             return
    #
    #     try:
    #         name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', ".", "Text (*.*)")[0]
    #         if name != '':
    #             file = open(name, 'r')
    #
    #             with file:
    #                 self.title = QtCore.QFileInfo(name).fileName()
    #                 self.text = file.read()
    #                 self.openEditor()
    #                 # self.pageManager.setCurrentIndex(2)
    #                 # self.worksheet.changeRecents(self, name, self.title)
    #                 # self.pageManager.setCurrentIndex(1)
    #                 # self.loadProgress.setValue(0)
    #
    #     except UnicodeError:
    #         QtWidgets.QMessageBox.question(self, 'File type not compatible',
    #                                        "Could not open file type\n"
    #                                        "My Notes can only open text files like '.txt', '.py', etc.",
    #                                        QtWidgets.QMessageBox.Ok)
    #     except FileNotFoundError:
    #         QtWidgets.QMessageBox.question(self, 'File not found',
    #                                        "Could not find the file \n Check if the file "
    #                                        "still exists and the path to it hasn't changed",
    #                                        QtWidgets.QMessageBox.Ok)

    def save(self):
        if self.titleInput.text() != '':
            self.title = self.titleInput.text()

        self.text = self.editor.toPlainText()
        with open(mainpath + "notes/" + self.title, 'w') as file:
            file.write(self.text)
            self.date = QtCore.QDateTime.currentDateTime()
        if internet_on() and len(self.notSynced) > 0:
            while len(self.notSynced) > 0:
                self.worksheet.saveNote('', self.notSynced[0], self.notSynced[1], self.notSynced[2])
                self.notSynced.remove(self.notSynced[0])
                self.notSynced.remove(self.notSynced[0])
                self.notSynced.remove(self.notSynced[0])

        if internet_on() and self.worksheet == None:
            self.worksheet = SpreadSheet()
            self.worksheet.saveNote('', self.title, self.text, self.date)
            # self.worksheet.saveNote(int(self.title.replace("New Note", '')) + 1, self.title, self.text, self.date)
        elif internet_on() and self.worksheet != None:
            self.worksheet.saveNote('', self.title, self.text, self.date)
            # self.worksheet.saveNote(int(self.title.replace("New Note", '')) + 1, self.title, self.text, self.date)
        else:
            QtWidgets.QMessageBox.question(self, 'No Internet',
                                           "Couldn't backup note to the cloud, due to no internet connection\n"
                                           "Notes will sync automatically when reconnected",
                                           QtWidgets.QMessageBox.Ok)
            self.notSynced.append(self.title)
            self.notSynced.append(self.text)
            self.notSynced.append(self.date)
        if self.express == True:
            sys.exit()
        self.setWindowTitle(self.title)

    def toolbarAction(self, icon, tooltip, action):
        extractAction = QtWidgets.QAction(self)
        if icon != '':
            extractAction.setIcon(QtGui.QIcon(icon))
        extractAction.setStatusTip(tooltip)
        if action != '':
            extractAction.triggered.connect(action)

        self.toolBar.addAction(extractAction)
        self.toolBar.setIconSize(QtCore.QSize(37, 37))
        return extractAction

    def menuAction(self, name, shortcut, action, submenu):
        extractAction = QtWidgets.QAction(name, self)
        extractAction.setShortcut(shortcut)
        extractAction.triggered.connect(action)

        submenu.addAction(extractAction)
        return extractAction

    def openEditor(self):
        if (self.editorOpened == False):
            self.editorOpened = True

            self.saveActionMenu.setEnabled(True)
            self.saveActionToolbar.setEnabled(True)

            self.editorAction.setEnabled(True)

            self.titleInput.setEnabled(True)

            self.pageManager.setCurrentIndex(1)

        self.setWindowTitle(self.title)
        self.editor.setPlainText(self.text)

    def exit(self):
        # os.remove(mainpath + "temp/lockfile.lock")
        QtWidgets.qApp.exit()

if __name__ == '__main__':
    # mainpath = os.path.expanduser('~') + "/.mynotes/"
    #if not os.path.exists(mainpath):
    #     os.makedirs(mainpath)
    #     os.makedirs(mainpath + "notes/")

    if not os.path.exists(mainpath + "notes/"):
        os.makedirs(mainpath + "notes/")

    # if os.path.isfile(mainpath + "temp/lockfile.lock"):
    #     sys.exit()
    # else:
    #     open(mainpath + "temp/lockfile.lock", 'w').write("running")
    app = QtWidgets.QApplication(sys.argv)
    win = Window()
    win.setMouseTracking(True)
    sys.exit(app.exec_())
