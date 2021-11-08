from PySide6.QtGui import QPixmap
import PySide6.QtWidgets as qtw
import PySide6.QtCore as qtc
import PySide6.QtGui as qtg
import PySide6.QtSvg as qtsvg
import PySide6.QtSvgWidgets as qtsvgw
from fuzzywuzzy import process
import sys
import shutil

from solver.solve import Problem
from solver.visualize import visualize

from . import game_parse
from .resources import ItemRate
from . import solve

OUTPUT_ICON = 'icons/Milestone/Recipe_Icon_Equipment_Dark.png'


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
        self.returnPressed.connect(
            lambda: self.select_item(0), qtc.Qt.QueuedConnection)
        input_search_comp.activated[qtc.QModelIndex].connect(
            lambda idx: self.select_item(idx.row()), qtc.Qt.DirectConnection)
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
        self.icon_label.setFixedSize(50, 50)
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
        if item is not None:
            self.setIcon(self.item.icon)
            self.group_box.setTitle(item.display)
        else:
            self.setIcon('')
            self.group_box.setTitle('')

    def setIcon(self, icon_path):
        self.icon = QPixmap(icon_path).scaledToHeight(
            50, qtc.Qt.SmoothTransformation)
        self.icon_label.setPixmap(self.icon)

    def getItem(self):
        return self.item

    def getRate(self):
        return self.group_widget.value()

    def triggerRemove(self, checked):
        if not checked:
            self.parentWidget().layout().removeWidget(self)
            self.deleteLater()


class TestWidget(qtw.QWidget):
    def __init__(self, scroll_area):
        super().__init__()
        self.scroll_area = scroll_area

    def resizeEvent(self, event):
        width = self.scroll_area.width() - self.scroll_area.viewport().width() + \
            event.size().width()
        print(f'Width: {width}')
        self.scroll_area.setMinimumWidth(width)


def main():
    game_data = game_parse.get_docs()
    items = game_data.items
    item_lookup = {item.display: item for item in items.values()}

    solution = None

    app = qtw.QApplication(sys.argv)
    w = qtw.QMainWindow()
    central_widget = qtw.QWidget()
    w.setCentralWidget(central_widget)
    w.setWindowTitle("Satisfactory Solver")
    w.resize(900, 600)

    wlayout = qtw.QHBoxLayout()
    central_widget.setLayout(wlayout)

    input_layout = qtw.QVBoxLayout()
    wlayout.addLayout(input_layout)

    input_search_box = ItemSearchWidget(None, item_lookup)
    input_layout.addWidget(input_search_box)

    input_scroll = qtw.QScrollArea()
    input_scroll.setWidgetResizable(True)
    input_scroll.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
    input_layout.addWidget(input_scroll)

    input_scroll_holdee = TestWidget(input_scroll)
    input_list = qtw.QVBoxLayout(input_scroll_holdee)
    input_scroll_holdee.setLayout(input_list)
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
    output_show_box.setIcon(OUTPUT_ICON)
    input_layout.addWidget(output_show_box)

    output_search_box.callback = output_show_box.setItem

    svg_scene = qtw.QGraphicsScene()
    svg_view = qtw.QGraphicsView(svg_scene)
    svg_item = qtsvgw.QGraphicsSvgItem()
    svg_renderer = qtsvg.QSvgRenderer()
    svg_item.setSharedRenderer(svg_renderer)
    svg_scene.addItem(svg_item)

    wlayout.addWidget(svg_view, 1)

    def go_fn():
        nonlocal solution
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
        visualize(solution, game_data, image_file='.temp.svg')
        print(svg_item)
        print(svg_item.renderer())
        svg_item.renderer().load('.temp.svg')
        svg_item.setElementId('')

    go_box.clicked.connect(go_fn)

    file_menu = w.menuBar().addMenu("&File")

    def clearWindow():
        nonlocal svg_renderer, solution
        solution = None
        svg_renderer.deleteLater()
        svg_renderer = qtsvg.QSvgRenderer()
        svg_item.setSharedRenderer(svg_renderer)
        while input_list.count() > 1:
            input_list.takeAt(0).widget().deleteLater()
        output_show_box.setItem(None)
        output_show_box.setIcon(OUTPUT_ICON)

    newAct = qtg.QAction('&New')
    newAct.setShortcut(qtg.QKeySequence.New)
    newAct.setStatusTip('Create a new Design')
    newAct.triggered.connect(clearWindow)
    file_menu.addAction(newAct)

    openAct = qtg.QAction('&Open')
    openAct.setShortcut(qtg.QKeySequence.Open)
    openAct.setStatusTip('Open an existing Design Plan')
    openAct.triggered.connect(lambda *args: print(f'Open File: {args}'))
    file_menu.addAction(openAct)

    saveAct = qtg.QAction('&Save Plan')
    saveAct.setShortcut(qtg.QKeySequence.Save)
    saveAct.setStatusTip('Save the Design Plan')
    saveAct.triggered.connect(lambda *args: print(f'Save Plan: {args}'))
    file_menu.addAction(saveAct)

    saveAsAct = qtg.QAction('Save Plan &As')
    saveAsAct.setShortcut(qtg.QKeySequence.SaveAs)
    saveAsAct.setStatusTip('Save the Design Plan As')
    saveAsAct.triggered.connect(lambda *args: print(f'Save As Plan: {args}'))
    file_menu.addAction(saveAsAct)

    def saveSvg():
        filename, img_kind = qtw.QFileDialog.getSaveFileName(
            w, "Save Implementation Image File", 'factory.svg', 'Vector Image (*.svg);;Raster Image (*.png)')
        visualize(solution, game_data, image_file=filename)

    svgAct = qtg.QAction('&Export Image')
    svgAct.setShortcut(qtg.QKeySequence(qtc.Qt.CTRL | qtc.Qt.Key_E))
    svgAct.setStatusTip('Save the implementation Image')
    svgAct.triggered.connect(saveSvg)
    file_menu.addAction(svgAct)

    w.show()
    sys.exit(app.exec_())
