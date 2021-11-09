from PySide6.QtGui import QPixmap, QWheelEvent
import PySide6.QtWidgets as qtw
import PySide6.QtCore as qtc
import PySide6.QtGui as qtg
import PySide6.QtSvg as qtsvg
import PySide6.QtSvgWidgets as qtsvgw
from fuzzywuzzy import process
import sys
import yaml

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


class WidthAnchor(qtw.QWidget):
    def __init__(self, scroll_area):
        super().__init__()
        self.scroll_area = scroll_area

    def resizeEvent(self, event):
        width = self.scroll_area.width() - self.scroll_area.viewport().width() + \
            event.size().width()
        self.scroll_area.setMinimumWidth(width)


class ZoomingGraphicsView(qtw.QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)

    # https://stackoverflow.com/questions/19113532/qgraphicsview-zooming-in-and-out-under-mouse-position-using-mouse-wheel
    def wheelEvent(self, event):
        modifiers = event.modifiers()
        if modifiers & qtc.Qt.ControlModifier:
            zoomInFactor = 1.25
            zoomOutFactor = 1 / zoomInFactor

            # Save the scene pos
            oldPos = event.position()
            unmapped_pos = self.mapFromScene(oldPos)

            # Zoom
            if event.angleDelta().y() > 0:
                zoomFactor = zoomInFactor
            else:
                zoomFactor = zoomOutFactor
            self.scale(zoomFactor, zoomFactor)

            # Get the new position
            newPos = self.mapToScene(unmapped_pos)

            # Move scene to old position
            delta = newPos - oldPos
            self.translate(delta.x(), delta.y())
        elif modifiers & qtc.Qt.ShiftModifier:
            angle_delta = qtc.QPoint(
                event.angleDelta().y(), event.angleDelta().x())
            pixel_delta = qtc.QPoint(
                event.pixelDelta().y(), event.pixelDelta().x())
            new_event = QWheelEvent(event.position(), event.globalPosition(), pixel_delta, angle_delta, event.buttons(
            ), modifiers & (~qtc.Qt.ShiftModifier), event.phase(), event.inverted(), event.source())
            super().wheelEvent(new_event)
        else:
            super().wheelEvent(event)


def main():
    game_data = game_parse.get_docs()
    items = game_data.items
    item_lookup = {item.display: item for item in items.values()}

    solution = None
    current_file = None

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

    input_scroll_holdee = WidthAnchor(input_scroll)
    input_list = qtw.QVBoxLayout(input_scroll_holdee)
    input_scroll_holdee.setLayout(input_list)
    input_list.insertStretch(-1)
    input_list.setSpacing(0)
    input_scroll.setWidget(input_scroll_holdee)

    def add_input(item, rate=0):
        widget = SchematicInputWidget(item, make_rate_box(rate))
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
    svg_view = ZoomingGraphicsView(svg_scene)
    svg_item = qtsvgw.QGraphicsSvgItem()
    svg_renderer = qtsvg.QSvgRenderer()
    svg_item.setSharedRenderer(svg_renderer)
    svg_scene.addItem(svg_item)

    wlayout.addWidget(svg_view, 1)

    def get_problem():
        if output_show_box.getItem() is None:
            return None
        target = output_show_box.getItem().id

        def get_item_box(index):
            return input_list.itemAt(index).widget()
        inputs = [
            ItemRate(get_item_box(i).getItem().id, get_item_box(i).getRate()) for i in range(input_list.count() - 1)
        ]
        return solve.Problem(target, inputs)

    def go_fn():
        nonlocal solution
        problem = get_problem()
        if problem is None:
            qtw.QMessageBox.warning(w, "Select a Target!",
                                    "Please select a target item before solving.")
            return
        solution = solve.optimize(problem, game_data)
        print(solution)
        visualize(solution, game_data, image_file='.temp.svg')
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

    def open_plan(direct=False):
        nonlocal current_file
        if not direct:
            current_file, file_type = qtw.QFileDialog.getOpenFileName(
                w, 'Open Factory Plan', '.', 'Factory Plan (*.yaml)'
            )
        with open(current_file, 'r') as file:
            plan = solve.Problem.from_dict(yaml.load(file))
        output_show_box.setItem(game_data.items[plan.target])
        for ir in plan.inputs:
            item = game_data.items[ir.resource]
            add_input(item, ir.rate)
        go_fn()

    openAct = qtg.QAction('&Open')
    openAct.setShortcut(qtg.QKeySequence.Open)
    openAct.setStatusTip('Open an existing Design Plan')
    openAct.triggered.connect(open_plan)
    file_menu.addAction(openAct)

    def save_plan(save_as):
        nonlocal current_file
        problem = get_problem()
        if problem is None:
            qtw.QMessageBox.warning(w, "Select a Target!",
                                    "Please select a target item before saving.")
            return
        if save_as or current_file is None:
            current_file, file_type = qtw.QFileDialog.getSaveFileName(
                w, "Save Factory Plan", 'factory.yaml', 'Factory Plan (*.yaml)')
        with open(current_file, 'w') as file:
            yaml.dump(problem.to_dict(), file)

    saveAct = qtg.QAction('&Save Plan')
    saveAct.setShortcut(qtg.QKeySequence.Save)
    saveAct.setStatusTip('Save the Design Plan')
    saveAct.triggered.connect(lambda: save_plan(False))
    file_menu.addAction(saveAct)

    saveAsAct = qtg.QAction('Save Plan &As')
    saveAsAct.setShortcut(qtg.QKeySequence.SaveAs)
    saveAsAct.setStatusTip('Save the Design Plan As')
    saveAsAct.triggered.connect(lambda: save_plan(True))
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

    quitAct = qtg.QAction('&Quit')
    quitAct.setShortcut(qtg.QKeySequence(qtc.Qt.CTRL | qtc.Qt.Key_Q))
    quitAct.setStatusTip('Quit the application')
    quitAct.triggered.connect(app.quit)  # TODO prompt for save
    file_menu.addAction(quitAct)

    if len(sys.argv) > 1:
        current_file = sys.argv[1]
        open_plan(True)

    w.show()
    sys.exit(app.exec_())
