import PySide6.QtWidgets as qtw
import PySide6.QtCore as qtc
from fuzzywuzzy import process
import sys

from . import game_parse
from . import resources


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

    input_scroll = qtw.QScrollArea()
    input_scroll.setWidgetResizable(True)
    input_scroll.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
    input_layout.addWidget(input_scroll)

    input_scroll_holdee = qtw.QWidget()
    input_list = qtw.QVBoxLayout(input_scroll_holdee)
    input_list.insertStretch(-1)
    input_scroll.setWidget(input_scroll_holdee)

    def add_input(button, idx):
        if not button.text():
            return  # Avoid double add
        print("Selected New Input:", button.completer().lst[idx])
        text = f'{button.completer().lst[idx]}'

        widget = qtw.QGroupBox()
        widget.setTitle(text)
        widget.setFlat(True)
        widget.setCheckable(True)
        layout = qtw.QHBoxLayout(widget)

        amount = qtw.QSpinBox()
        layout.addWidget(amount)

        remove = qtw.QPushButton()
        layout.addWidget(remove)

        input_list.insertWidget(input_list.count() - 1, widget)
        button.clear()

    svg_view = qtw.QGraphicsView()
    wlayout.addWidget(svg_view)

    w.show()
    sys.exit(app.exec_())
