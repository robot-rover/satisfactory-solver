from PySide6.QtGui import QPixmap
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
        l = process.extractBests(self.term, self.items.keys(), limit=20)
        self.lst = [self.items[display] for display, value in l]
        model = qtc.QStringListModel()
        model.setStringList(t[0] for t in l)
        self.setModel(model)

    def pathFromIndex(self, index):
        return ""  # self.lst[index.row()]

    def splitPath(self, path):
        self.setCompletionPrefix(path)
        return []


class SchematicInputWidget(qtw.QWidget):
    def __init__(self, item, rate):
        super().__init__()
        self.item = item
        self.rate = rate

        layout = qtw.QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.icon = QPixmap(self.item.icon).scaledToHeight(
            50, qtc.Qt.SmoothTransformation)
        icon_label = qtw.QLabel()
        icon_label.setPixmap(self.icon)
        layout.addWidget(icon_label, 0)

        group_box = qtw.QGroupBox()
        group_box.setTitle(item.display)
        group_box.setCheckable(True)
        layout.addWidget(group_box, 1)

        group_layout = qtw.QHBoxLayout()
        amount = qtw.QSpinBox()
        amount.setMaximum(2**31-1)
        amount.setMinimum(-2**31)
        group_layout.addWidget(amount)
        group_box.setLayout(group_layout)

        group_box.toggled.connect(self.triggerRemove)

    def triggerRemove(self, checked):
        if not checked:
            self.parentWidget().layout().removeWidget(self)
            self.deleteLater()


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
        input_search_box, {item.display: item for item in item_lookup.values()})
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
    input_list.setSpacing(0)
    input_scroll.setWidget(input_scroll_holdee)

    def add_input(button, idx):
        if not button.text():
            return  # Avoid double add
        print("Selected New Input:", button.completer().lst[idx])
        item = button.completer().lst[idx]
        widget = SchematicInputWidget(item, 0.0)

        input_list.insertWidget(input_list.count() - 1, widget)
        button.clear()

    svg_view = qtw.QGraphicsView()
    wlayout.addWidget(svg_view)

    w.show()
    sys.exit(app.exec_())
