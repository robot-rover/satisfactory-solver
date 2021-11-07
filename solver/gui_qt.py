from PySide6.QtGui import QPixmap
import PySide6.QtWidgets as qtw
import PySide6.QtCore as qtc
from fuzzywuzzy import process
import sys

from solver.solve import Problem

from . import game_parse
from .resources import ItemRate
from . import solve


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

class ItemSearchWidget(qtw.QLineEdit):
    def __init__(self, callback, items):
        super().__init__()
        self.callback = callback

        input_search_comp = FuzzyQCompleter(
            self, items)
        input_search_comp.setCompletionMode(
            qtw.QCompleter.CompletionMode.PopupCompletion)
        input_search_comp.setModelSorting(
            qtw.QCompleter.ModelSorting.UnsortedModel)
        # Ensure the complete activation goes before the return button
        self.returnPressed.connect(lambda: self.select_item(0), qtc.Qt.QueuedConnection)
        input_search_comp.activated[qtc.QModelIndex].connect(lambda idx: self.select_item(idx.row()), qtc.Qt.DirectConnection)
        self.setCompleter(input_search_comp)

    def select_item(self, idx):
        if not self.text():
            return  # Avoid double add
        item = self.completer().lst[idx]

        self.callback(item)
        self.clear()

def make_rate_box(rate):
    group_widget = qtw.QSpinBox()
    group_widget.setMaximum(2**31-1)
    group_widget.setMinimum(-2**31)
    group_widget.setValue(rate)
    return group_widget

class SchematicInputWidget(qtw.QWidget):
    def __init__(self, item, group_widget, check_delete=True):
        super().__init__()
        self.item = None
        self.group_widget = group_widget

        layout = qtw.QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.icon_label = qtw.QLabel()
        self.icon_label.setFixedSize(50,50)
        layout.addWidget(self.icon_label, 0)

        self.group_box = qtw.QGroupBox()
        layout.addWidget(self.group_box, 1)

        group_layout = qtw.QHBoxLayout()
        group_layout.addWidget(self.group_widget)
        self.group_box.setLayout(group_layout)

        if check_delete:
            self.group_box.setCheckable(True)
            self.group_box.toggled.connect(self.triggerRemove)
        if item is not None:
            self.setItem(item)

    def setItem(self, item):
        self.item = item
        self.icon = QPixmap(self.item.icon).scaledToHeight(
            50, qtc.Qt.SmoothTransformation)
        self.icon_label.setPixmap(self.icon)
        self.group_box.setTitle(item.display)

    def getItem(self):
        return self.item

    def getRate(self):
        return self.group_widget.value()


    def triggerRemove(self, checked):
        if not checked:
            self.parentWidget().layout().removeWidget(self)
            self.deleteLater()

def main():
    game_data = game_parse.get_docs()
    items = game_data.items
    item_lookup = {item.display: item for item in items.values()}

    app = qtw.QApplication(sys.argv)
    w = qtw.QWidget()
    w.setWindowTitle("Satisfactory Solver")
    w.resize(900, 600)

    wlayout = qtw.QHBoxLayout()
    w.setLayout(wlayout)

    input_layout = qtw.QVBoxLayout()
    wlayout.addLayout(input_layout)

    input_search_box = ItemSearchWidget(None, item_lookup)
    input_layout.addWidget(input_search_box)

    input_scroll = qtw.QScrollArea()
    input_scroll.setWidgetResizable(True)
    input_scroll.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
    input_layout.addWidget(input_scroll)

    input_scroll_holdee = qtw.QWidget()
    input_list = qtw.QVBoxLayout(input_scroll_holdee)
    input_list.insertStretch(-1)
    input_list.setSpacing(0)
    input_scroll.setWidget(input_scroll_holdee)

    def add_input(item):
        widget = SchematicInputWidget(item, make_rate_box(0))

        input_list.insertWidget(input_list.count() - 1, widget)
    
    input_search_box.callback = add_input

    output_search_box = ItemSearchWidget(None, item_lookup)
    input_layout.addWidget(output_search_box)
    go_box = qtw.QPushButton("Go!")
    output_show_box = SchematicInputWidget(None, go_box, False)
    input_layout.addWidget(output_show_box)

    output_search_box.callback = output_show_box.setItem

    def go_fn():
        target = output_show_box.getItem().id
        def get_item_box(index):
            return input_list.itemAt(index).widget()
        inputs = [
            ItemRate(get_item_box(i).getItem().id, get_item_box(i).getRate()) for i in range(input_list.count() - 1)
        ]
        print('Inputs:', inputs)
        problem = solve.Problem(target, inputs)
        solution = solve.optimize(problem, game_data)
        print(solution)


    go_box.clicked.connect(go_fn)

    svg_view = qtw.QGraphicsView()
    wlayout.addWidget(svg_view)

    w.show()
    sys.exit(app.exec_())
