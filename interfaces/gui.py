#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from PyQt4 import QtGui
from PyQt4 import QtCore
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s
from interfaces.common import *
import interfaces.qtGui

class TableModel(QtCore.QAbstractTableModel):
	def __init__(self):
		super(TableModel, self).__init__()
		self.animeList = []
		self.headers = ["Title","Genre","Status","Watched","Observations"]
		self.active_file = ""

	def columnCount(self, parent = QtCore.QModelIndex()):
		return 5

	def data(self, index, role = QtCore.Qt.DisplayRole):
		if index.isValid() == False:
			return QtCore.QVariant()
		if index.row() >= self.rowCount() or index.row() < 0:
			return QtCore.QVariant()

		if role == QtCore.Qt.DisplayRole:
			if index.column() == 0:
				return self.animeList[index.row()][0]
			elif index.column() == 1:
				return self.animeList[index.row()][1]
			elif index.column() == 2:
				return self.animeList[index.row()][2]
			elif index.column() == 3:
				return self.animeList[index.row()][3]
			elif index.column() == 4:
				return self.animeList[index.row()][4]

		return QtCore.QVariant()

	def getAnimeNames(self):
		names = []
		for anime in self.animeList:
			names.append(anime[0])
		return names

	def headerData(self, column, orientation, role = QtCore.Qt.DisplayRole):
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return QtCore.QVariant(self.headers[column])
		return QtCore.QVariant()

	def rowCount(self, parent = QtCore.QModelIndex()):
		return len(self.animeList)

	def load_db(self, filename):
		self.active_file = filename
		self.db = Parser(filename)
		for entry in self.db.dictionary['items']:
			self.animeList.append([entry["name"], entry["genre"], translated_status[entry['type'].lower()][entry["status"].lower()], entry["lastwatched"], entry["obs"]])

class AddEntryDialog(QtGui.QDialog):
	def __init__(self, parent = None):
		QtGui.QDialog.__init__(self, parent)
		self.setupUi()
		self.setModal(True)

		QtCore.QObject.connect(self.pushButton_2, QtCore.SIGNAL(_fromUtf8("clicked()")), self.close)
		QtCore.QObject.connect(self.titleLine, QtCore.SIGNAL(_fromUtf8("editingFinished()")), self.populateCB)
		QtCore.QObject.connect(self.selectCB, QtCore.SIGNAL(_fromUtf8("currentIndexChanged()")), self.animeSelected)
		QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), self.addAnime)

	def setupUi(self):
		self.layout = QtGui.QGridLayout()

		self.titleLabel = QtGui.QLabel("Title:")
		self.titleLine = QtGui.QLineEdit()
		self.titleLayout = QtGui.QHBoxLayout()
		self.titleLayout.addWidget(self.titleLabel)
		self.titleLayout.addWidget(self.titleLine)

		self.typeLabel = QtGui.QLabel("Type:")
		self.animeButton = QtGui.QRadioButton("Anime")
		self.mangaButton = QtGui.QRadioButton("Manga")
		self.typeLayout = QtGui.QHBoxLayout()
		self.typeLayout.addWidget(self.typeLabel)
		self.typeLayout.addWidget(self.animeButton)
		self.typeLayout.addWidget(self.mangaButton)

		self.selectLabel = QtGui.QLabel("Select Search Item:")
		self.selectCB = QtGui.QComboBox()
		self.selectLayout = QtGui.QHBoxLayout()
		self.selectLayout.addWidget(self.selectLabel)
		self.selectLayout.addWidget(self.selectCB)

		self.statusLabel = QtGui.QLabel("Status:")
		self.statusCB = QtGui.QComboBox()
		self.statusCB.addItem("Watched")
		self.statusCB.addItem("Queued")
		self.statusCB.addItem("Dropped")
		self.statusCB.addItem("Watching")
		self.statusCB.addItem("On Hold")
		self.statusLayout = QtGui.QHBoxLayout()
		self.statusLayout.addWidget(self.statusLabel)
		self.statusLayout.addWidget(self.statusCB)

		self.lwLabel = QtGui.QLabel("Episodes Watched/Chapters Read:")
		self.lwLine = QtGui.QLineEdit()
		self.lwLayout = QtGui.QHBoxLayout()
		self.lwLayout.addWidget(self.lwLabel)
		self.lwLayout.addWidget(self.lwLine)

		self.obsLabel = QtGui.QLabel("Observations:")
		self.obsLine = QtGui.QLineEdit()
		self.obsLayout = QtGui.QHBoxLayout()
		self.obsLayout.addWidget(self.obsLabel)
		self.obsLayout.addWidget(self.obsLine)

		self.pushButton = QtGui.QPushButton("Add Entry")
		self.pushButton_2 = QtGui.QPushButton("Cancel")
		self.buttonLayout = QtGui.QHBoxLayout()
		self.buttonLayout.addWidget(self.pushButton)
		self.buttonLayout.addWidget(self.pushButton_2)

		self.layout.addItem(self.titleLayout)
		self.layout.addItem(self.typeLayout)
		self.layout.addItem(self.selectLayout)
		self.layout.addItem(self.statusLayout)
		self.layout.addItem(self.lwLayout)
		self.layout.addItem(self.obsLayout)
		self.layout.addItem(self.buttonLayout)
		self.setLayout(self.layout)

	def populateCB(self):
		self.selectCB.clear()
		title = self.titleLine.text()
		if self.animeButton.isChecked() == True:
			search_results = utils.MALWrapper.search(title, "anime")
		else:
			search_results = utils.MALWrapper.search(title, "manga")
		for result in search_results:
			self.selectCB.addItem(str(result["title"]))
		self.results = search_results

	def animeSelected(self, index):
		print "test"
		print index

	def addAnime(self):
		return

class DeleteEntryDialog(QtGui.QDialog):
	def __init__(self, parent = None, names = []):
		QtGui.QDialog.__init__(self, parent)
		self.setupUi()
		self.setModal(True)

		self.comboBox.addItems(names)
		QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), self.setReturnCode)
		QtCore.QObject.connect(self.pushButton_2, QtCore.SIGNAL(_fromUtf8("clicked()")), self.close)
		
	def setupUi(self):
		self.layout = QtGui.QHBoxLayout()
		self.pushButton = QtGui.QPushButton("Delete")
		self.pushButton_2 = QtGui.QPushButton("Cancel")
		self.comboBox = QtGui.QComboBox()
			
		self.layout.addWidget(self.comboBox)
		self.layout.addWidget(self.pushButton)
		self.layout.addWidget(self.pushButton_2)
		self.setLayout(self.layout)

	def setReturnCode(self):
		# add one to the index since QDialog already uses the 0
		# return code to signify normal closing
		self.done(self.comboBox.currentIndex() + 1)

class SwapEntryDialog(QtGui.QDialog):
	def __init__(self, parent = None, names = []):
		QtGui.QDialog.__init__(self, parent)
		self.setupUi()
		self.setModal(True)
		self.model = model
		self.ui = ui

		self.entry1Box.addItems(names)
		self.entry2Box.addItems(names)
		QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), self.swap)
		QtCore.QObject.connect(self.pushButton_2, QtCore.SIGNAL(_fromUtf8("clicked()")), self.close)
		
	def setupUi(self):
		self.layout = QtGui.QHBoxLayout()
		self.pushButton = QtGui.QPushButton("Swap")
		self.pushButton_2 = QtGui.QPushButton("Cancel")
		self.entry1Box = QtGui.QComboBox()
		self.entry2Box = QtGui.QComboBox()

		self.layout.addWidget(self.entry1Box)
		self.layout.addWidget(self.entry2Box)
		self.layout.addWidget(self.pushButton)
		self.layout.addWidget(self.pushButton_2)
		self.setLayout(self.layout)

	def swap(self):
		entry1 = self.entry1Box.currentIndex()
		entry2 = self.entry2Box.currentIndex()
		if entry1 == entry2:
			self.done(0)
		doSwap(entry1, entry2)
		self.done(0)

def openFile():
	global model
	filename = QtGui.QFileDialog.getOpenFileName(None, "Open Data File", "", "Futaam Database (*.db);; All Files (*)")
	if filename != None:
		model = TableModel()
		model.load_db(filename)
		ui.tableView.setModel(model)

def deleteEntry():
	global model
	global ui
	animeNames = model.getAnimeNames()
	
	dialog = DeleteEntryDialog(parent=ui.centralwidget, names=animeNames)
	toDelete = dialog.exec_()
	if toDelete == 0:
		return
	# see comment in DeleteEntryDialog.setReturnCode()
	toDelete = toDelete - 1
	for entry in model.db.dictionary['items']:
		if entry['id'] == toDelete:
			model.db.dictionary['items'].remove(entry)
			model.db.dictionary['count'] -= 1
			model.db.save()
			break
	rebuildIds()
	reloadTable()

def addEntry():
	global model
	global ui
	
	dialog = AddEntryDialog(parent=ui.centralwidget)
	dialog.exec_()

def swapEntries():
	global model
	global ui
	animeNames = model.getAnimeNames()

	dialog = SwapEntryDialog(names=animeNames, parent=ui.centralwidget)
	dialog.exec_()

def doSwap(index1, index2):
	global model
	global ui

	entry1 = model.db.dictionary['items'][index1]
	entry2 = model.db.dictionary['items'][index2]
	model.db.dictionary['items'][index1] = entry2
	model.db.dictionary['items'][index2] = entry1
	model.db.save()
	rebuildIds()
	reloadTable()

def rebuildIds():
	global model
	for x in xrange(0, model.db.dictionary['count']):
		model.db.dictionary['items'][x]['id'] = x

def reloadTable():
	global model
	global ui
	filename = model.active_file
	model = TableModel()
	model.load_db(filename)
	ui.tableView.setModel(model)
			
def main(argv):
	global model
	global ui
	app = QtGui.QApplication(argv)
	window = QtGui.QMainWindow()
	ui = interfaces.qtGui.Ui_Futaam()
	ui.setupUi(window)

	model = TableModel()
	if len(argv) == 0:
		help()
	model.load_db(argv[0])
	ui.tableView.setModel(model)

	QtCore.QObject.connect(ui.actionQuit, QtCore.SIGNAL(_fromUtf8("triggered()")), window.close)
	QtCore.QObject.connect(ui.actionOpen, QtCore.SIGNAL(_fromUtf8("triggered()")), openFile)
	QtCore.QObject.connect(ui.actionSave, QtCore.SIGNAL(_fromUtf8("triggered()")), model.db.save)
	QtCore.QObject.connect(ui.actionDelete_Entry, QtCore.SIGNAL(_fromUtf8("triggered()")), deleteEntry)
	QtCore.QObject.connect(ui.actionAdd_Entry, QtCore.SIGNAL(_fromUtf8("triggered()")), addEntry)
	QtCore.QObject.connect(ui.actionSwap_Entries, QtCore.SIGNAL(_fromUtf8("triggered()")), swapEntries)
	
	window.show()
	exit(app.exec_())

def help():
	print """USAGE: ./futaam.py --gui [DATABASE]"""
	quit()
