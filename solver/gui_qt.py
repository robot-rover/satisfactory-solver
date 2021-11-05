import PySide6.QtWidgets as qtw
import PySide6.QtCore as qtc
from fuzzywuzzy import process
import sys

from . import game_parse
from . import resources


class ItemRateModel(qtc.QAbstractListModel):
    def __init__(self):
        super().__init__()
        self.lst = []

    def rowCount(self, parent=None):
        return len(self.lst)

    def data(self, index, role=None):
        tup = self.lst[index.row()]
        if(role == qtc.Qt.EditRole):
            return tup[1]
        if(role == qtc.Qt.DisplayRole):
            return tup[2]
        return None

    def setData(self, index, value, role=None):
        tup = self.lst[index.row()]
        if role == qtc.Qt.ItemDataRole.EditRole:
            self.lst[index.row()] = (tup[0], float(value), tup[2])
        elif role == qtc.Qt.DisplayRole:
            self.lst[index.row()] = (value, tup[1], tup[2])
        else:
            self.lst[index.row()] = (value[0], value[1], tup[2])
        self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        return qtc.Qt.ItemIsEnabled | qtc.Qt.ItemIsEditable

    def insertRows(self, row, count, parent):
        self.beginInsertRows(parent, row, row + count - 1)
        end_rev = []
        while(len(self.lst)) > row:
            end_rev.append(self.lst.pop())
        for _ in range(count):
            self.lst.append(("", 0.0, qtw.QSpinBox()))
        self.lst.extend(end_rev[::-1])
        self.endInsertRows()
        return True


class ItemRateDelegate(qtw.QStyledItemDelegate):
    def __init__(self):
        super().__init__()

    def createEditor(self, parent, option, index):
        editor = qtw.QWidget(parent)
        layout = qtw.QHBoxLayout()
        editor.setLayout(layout)

        # text = qtw.QLabel()
        # layout.addWidget(text)

        spin = qtw.QSpinBox()
        spin.setFrame(False)
        spin.setMinimum(0)
        layout.addWidget(spin)
        return editor

    def setEditorData(self, editor, index):
        print('setEditor')
        # value = index.model().data(index, qtc.Qt.EditRole)
        # editor.layout().itemAt(1).widget().setValue(value)

    def setModelData(self, editor, model, index):
        print('setModel')
        # value = editor.layout().itemAt(1).widget().value()
        # model.setData(index, value, qtc.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        print('geometry')
        editor.layout().setGeometry(option.rect)


class FuzzyQCompleter(qtw.QCompleter):
    def __init__(self, parent, items):
        super().__init__(parent=parent)
        self.term = ""
        self.items = items

    def setCompletionPrefix(self, term):
        self.term = term
        self.completion()

    def completion(self):
        l = process.extractBests(self.term, self.items, limit=20)
        model = qtc.QStringListModel()
        self.lst = [t[0] for t in l]
        model.setStringList(self.lst)
        self.setModel(model)

    def pathFromIndex(self, index):
        return ""  # self.lst[index.row()]

    def splitPath(self, path):
        self.setCompletionPrefix(path)
        return []


def main():
    recipes, items = game_parse.get_docs()
    item_lookup = {item.display: item for item in items.values()}

    input_model = ItemRateModel()

    def add_input(button, idx):
        if not button.text():
            return  # Avoid double add
        print("Selected New Input:", button.completer().lst[idx])
        model_index = input_model.rowCount()
        input_model.insertRow(model_index)
        input_model.setData(input_model.createIndex(
            model_index, 0), (button.completer().lst[idx], 0.0))
        button.clear()

    app = qtw.QApplication(sys.argv)
    w = qtw.QWidget()
    w.setWindowTitle("Satisfactory Solver")

    wlayout = qtw.QHBoxLayout()
    w.setLayout(wlayout)

    input_layout = qtw.QVBoxLayout()
    wlayout.addLayout(input_layout)

    input_search_box = qtw.QLineEdit()
    input_layout.addWidget(input_search_box)

    input_search_comp = FuzzyQCompleter(
        input_search_box, list(item_lookup.keys()))
    input_search_comp.setCompletionMode(
        qtw.QCompleter.CompletionMode.PopupCompletion)
    input_search_comp.setModelSorting(
        qtw.QCompleter.ModelSorting.UnsortedModel)
    # Ensure the complete activation goes before the return button
    input_search_box.returnPressed.connect(lambda: add_input(
        input_search_box, 0), qtc.Qt.QueuedConnection)
    input_search_comp.activated[qtc.QModelIndex].connect(
        lambda idx: add_input(input_search_box, idx.row()), qtc.Qt.DirectConnection)
    input_search_box.setCompleter(input_search_comp)

    input_list = qtw.QListView()
    input_list.setModel(input_model)
    input_list.setItemDelegate(ItemRateDelegate())
    input_layout.addWidget(input_list)

    svg_view = qtw.QGraphicsView()
    wlayout.addWidget(svg_view)

    w.show()
    sys.exit(app.exec_())
