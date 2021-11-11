import math

import PySide6.QtWidgets as qtw
import PySide6.QtCore as qtc
import PySide6.QtGui as qtg
import PySide6.QtSvg as qtsvg
import PySide6.QtSvgWidgets as qtsvgw
from fuzzywuzzy import process
import sys
import yaml


from . import game_parse, solve, visualize
from .resources import ItemRate
from .gui_recipes import AlternateRecipeWindow

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
    def __init__(self, default_text, items, shortcut=None):
        super().__init__()
        self.callback = None
        self.setPlaceholderText(default_text)

        self.shortcut = shortcut
        if self.shortcut is not None:
            self.shortcut.activated.connect(
                lambda: self.setFocus(qtc.Qt.ShortcutFocusReason))

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


class SchematicInputWidget(qtw.QWidget):
    def __init__(self, item, group_widget, check_delete=True):
        super().__init__()
        self.item = None
        self.group_widget = group_widget
        self.setFocusProxy(self.group_widget)

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

    @classmethod
    def with_spinbox(cls, item, rate):
        group_widget = SchematicInputWidget.make_rate_box(rate)
        return cls(item, group_widget)

    @staticmethod
    def make_rate_box(rate):
        group_widget = qtw.QSpinBox()
        group_widget.setMaximum(2**31-1)
        group_widget.setMinimum(-2**31)
        group_widget.setValue(rate)
        return group_widget

    def setItem(self, item):
        self.item = item
        if item is not None:
            self.setIcon(self.item.icon)
            self.group_box.setTitle(item.display)
        else:
            self.setIcon('')
            self.group_box.setTitle('')

    def setIcon(self, icon_path):
        self.icon = qtg.QPixmap(icon_path).scaledToHeight(
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

    def wheelEvent(self, event):
        modifiers = event.modifiers()
        if modifiers & qtc.Qt.ControlModifier:
            # https://stackoverflow.com/questions/19113532/qgraphicsview-zooming-in-and-out-under-mouse-position-using-mouse-wheel
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
            # Implement Horizontal Scrolling
            angle_delta = qtc.QPoint(
                event.angleDelta().y(), event.angleDelta().x())
            pixel_delta = qtc.QPoint(
                event.pixelDelta().y(), event.pixelDelta().x())
            new_event = qtg.QWheelEvent(event.position(), event.globalPosition(), pixel_delta, angle_delta, event.buttons(
            ), modifiers & (~qtc.Qt.ShiftModifier), event.phase(), event.inverted(), event.source())
            super().wheelEvent(new_event)
        else:
            # Default to Vertical Scrolling
            super().wheelEvent(event)


class SatisfactorySolverMain(qtw.QApplication):
    def __init__(self, args):
        super().__init__(args)
        self.game_data = game_parse.get_docs()
        self.item_lookup = {
            item.display: item for item in self.game_data.items.values()}

        self.solution = None
        self.current_file = None

        self.w = qtw.QMainWindow()
        self.central_widget = qtw.QWidget()
        self.w.setCentralWidget(self.central_widget)
        self.w.setWindowTitle("Satisfactory Solver")
        self.w.resize(900, 600)

        self.center_layout = qtw.QHBoxLayout()
        self.central_widget.setLayout(self.center_layout)

        self.input_layout = qtw.QVBoxLayout()
        self.center_layout.addLayout(self.input_layout)

        self.input_search_box = ItemSearchWidget(
            'Add Input', self.item_lookup, qtg.QShortcut(qtg.QKeySequence(qtc.Qt.CTRL | qtc.Qt.Key_I), self.w))
        self.input_layout.addWidget(self.input_search_box)

        self.input_scroll = qtw.QScrollArea()
        self.input_scroll.setWidgetResizable(True)
        self.input_scroll.setHorizontalScrollBarPolicy(
            qtc.Qt.ScrollBarAlwaysOff)
        self.input_layout.addWidget(self.input_scroll)

        self.input_scroll_holdee = WidthAnchor(self.input_scroll)
        self.input_scroll.setFocusProxy(self.input_scroll_holdee)
        self.input_list = qtw.QVBoxLayout(self.input_scroll_holdee)
        self.input_scroll_holdee.setLayout(self.input_list)
        self.input_list.insertStretch(-1)
        self.input_list.setSpacing(0)
        self.input_scroll.setWidget(self.input_scroll_holdee)

        self.input_search_box.callback = self.add_input

        self.output_search = ItemSearchWidget(
            'Set Target', self.item_lookup, qtg.QShortcut(qtg.QKeySequence(qtc.Qt.CTRL | qtc.Qt.Key_T), self.w))
        self.input_layout.addWidget(self.output_search)
        self.go_box = qtw.QPushButton("Go!")
        self.output_show_box = SchematicInputWidget(None, self.go_box, False)
        self.output_show_box.setIcon(OUTPUT_ICON)
        self.input_layout.addWidget(self.output_show_box)

        self.output_search.callback = self.output_show_box.setItem

        self.svg_scene = qtw.QGraphicsScene()
        self.svg_view = ZoomingGraphicsView(self.svg_scene)
        self.svg_item = qtsvgw.QGraphicsSvgItem()
        self.svg_renderer = qtsvg.QSvgRenderer()
        self.svg_item.setSharedRenderer(self.svg_renderer)
        self.svg_scene.addItem(self.svg_item)

        self.center_layout.addWidget(self.svg_view, 1)

        self.go_box.clicked.connect(self.go_fn)
        self.go_box.setShortcut(qtg.QKeySequence(
            qtc.Qt.CTRL | qtc.Qt.Key_G))

        self.recipe_window = AlternateRecipeWindow(self.game_data)

        self.set_tab_order()

        self.setup_menu()

        if len(args) > 1:
            self.current_file = args[1]
            self.open_plan(True)

    def setup_menu(self):
        self.file_menu = self.w.menuBar().addMenu("&File")
        self.file_menu_actions = []

        newAct = qtg.QAction('&New')
        newAct.setShortcut(qtg.QKeySequence.New)
        newAct.setStatusTip('Create a new Design')
        newAct.triggered.connect(self.clearWindow)
        self.file_menu.addAction(newAct)
        self.file_menu_actions.append(newAct)

        openAct = qtg.QAction('&Open')
        openAct.setShortcut(qtg.QKeySequence.Open)
        openAct.setStatusTip('Open an existing Design Plan')
        openAct.triggered.connect(self.open_plan)
        self.file_menu.addAction(openAct)
        self.file_menu_actions.append(openAct)

        saveAct = qtg.QAction('&Save Plan')
        saveAct.setShortcut(qtg.QKeySequence.Save)
        saveAct.setStatusTip('Save the Design Plan')
        saveAct.triggered.connect(lambda: self.save_plan(False))
        self.file_menu.addAction(saveAct)
        self.file_menu_actions.append(saveAct)

        saveAsAct = qtg.QAction('Save Plan &As')
        saveAsAct.setShortcut(qtg.QKeySequence.SaveAs)
        saveAsAct.setStatusTip('Save the Design Plan As')
        saveAsAct.triggered.connect(lambda: self.save_plan(True))
        self.file_menu.addAction(saveAsAct)
        self.file_menu_actions.append(saveAsAct)

        svgAct = qtg.QAction('&Export Image')
        svgAct.setShortcut(qtg.QKeySequence(qtc.Qt.CTRL | qtc.Qt.Key_E))
        svgAct.setStatusTip('Save the implementation Image')
        svgAct.triggered.connect(self.saveSvg)
        self.file_menu.addAction(svgAct)
        self.file_menu_actions.append(svgAct)

        quitAct = qtg.QAction('&Quit')
        quitAct.setShortcut(qtg.QKeySequence(qtc.Qt.CTRL | qtc.Qt.Key_Q))
        quitAct.setStatusTip('Quit the application')
        quitAct.triggered.connect(self.quit)  # TODO prompt for save
        self.file_menu.addAction(quitAct)
        self.file_menu_actions.append(quitAct)

        self.edit_menu = self.w.menuBar().addMenu("&Edit")
        self.edit_menu_actions = []

        recipeAct = qtg.QAction('Enabled &Recipes')
        recipeAct.setStatusTip('Edit the Enabled Recipes')
        recipeAct.triggered.connect(self.recipe_window.show)
        self.edit_menu.addAction(recipeAct)
        self.edit_menu_actions.append(recipeAct)

        self.distAct = qtg.QAction('&Distribute Machines')
        self.distAct.setStatusTip(
            'Show a recipe quantity distributed across an integer number of machines')
        self.distAct.setCheckable(True)
        self.distAct.triggered.connect(self.go_fn)
        self.edit_menu.addAction(self.distAct)
        self.edit_menu_actions.append(self.distAct)

        excessAct = qtg.QAction('Remove &Excess')
        excessAct.setStatusTip('Remove excess Inputs from Plan')
        excessAct.triggered.connect(self.remove_excess_inputs)
        self.edit_menu.addAction(excessAct)
        self.edit_menu_actions.append(excessAct)

    def set_tab_order(self):
        qtw.QWidget.setTabOrder(self.input_search_box,
                                self.input_scroll_holdee)
        qtw.QWidget.setTabOrder(self.input_scroll_holdee, self.output_search)
        qtw.QWidget.setTabOrder(self.output_search, self.go_box)
        qtw.QWidget.setTabOrder(self.go_box, self.input_search_box)

    def clearWindow(self):
        self.solution = None
        self.svg_renderer.deleteLater()
        self.svg_renderer = qtsvg.QSvgRenderer()
        self.svg_item.setSharedRenderer(self.svg_renderer)
        while self.input_list.count() > 1:
            self.input_list.takeAt(0).widget().deleteLater()
        self.output_show_box.setItem(None)
        self.output_show_box.setIcon(OUTPUT_ICON)

    def iterate_input_widgets(self):
        return (self.input_list.itemAt(i).widget() for i in range(self.input_list.count() - 1))

    def add_input(self, item, rate=0):
        for item_widget in self.iterate_input_widgets():
            if item_widget.getItem().id == item.id:
                item_widget.group_widget.setValue(
                    item_widget.group_widget.value() + rate)
                return
        widget = SchematicInputWidget.with_spinbox(item, rate)
        self.input_list.insertWidget(self.input_list.count() - 1, widget)

    def get_problem(self):
        if self.output_show_box.getItem() is None:
            return None
        target = self.output_show_box.getItem().id

        inputs = [
            ItemRate(item_box.getItem().id, item_box.getRate()) for item_box in
            self.iterate_input_widgets()
        ]
        return solve.Problem(target, inputs)

    def go_fn(self):
        problem = self.get_problem()
        if problem is None:
            qtw.QMessageBox.warning(self.w, "Select a Target!",
                                    "Please select a target item before solving.")
            return
        self.solution = solve.optimize(
            problem, self.game_data, self.recipe_window.to_recipe_config())
        print(self.solution)
        visualize.visualize(self.solution, self.game_data, image_file='.temp.svg',
                            recipe_distribute=self.distAct.isChecked())
        self.svg_renderer.load('.temp.svg')
        self.svg_item.setElementId('')

    def remove_excess_inputs(self):
        self.go_fn()
        if self.solution is None:
            return
        for output_ir in self.solution.outputs:
            for input_widget in self.iterate_input_widgets():
                if output_ir.resource == input_widget.item.id:
                    input_widget.group_widget.setValue(
                        input_widget.group_widget.value() - math.floor(output_ir.rate))
        self.go_fn()

    def open_plan(self, direct=False):
        if not direct:
            file_name, file_type = qtw.QFileDialog.getOpenFileName(
                self.w, 'Open Factory Plan', '.', 'Factory Plan (*.yaml)'
            )
            if file_name == '':
                return
            self.current_file = file_name
        with open(self.current_file, 'r') as file:
            plan = solve.Problem.from_dict(yaml.load(file))
        self.clearWindow()
        self.output_show_box.setItem(self.game_data.items[plan.target])
        for ir in plan.inputs:
            item = self.game_data.items[ir.resource]
            self.add_input(item, ir.rate)
        self.go_fn()

    def save_plan(self, save_as):
        problem = self.get_problem()
        if problem is None:
            qtw.QMessageBox.warning(self.w, "Select a Target!",
                                    "Please select a target item before saving.")
            return
        if save_as or self.current_file is None:
            file_name, file_type = qtw.QFileDialog.getSaveFileName(
                self.w, "Save Factory Plan", 'factory.yaml', 'Factory Plan (*.yaml)')
            if file_name == '':
                return
            self.current_file = file_name
        with open(self.current_file, 'w') as file:
            yaml.dump(problem.to_dict(), file)

    def saveSvg(self):
        filename, img_kind = qtw.QFileDialog.getSaveFileName(
            self.w, "Save Implementation Image File", 'factory.svg', 'Vector Image (*.svg);;Raster Image (*.png)')
        if filename == '':
            return
        visualize(self.solution, self.game_data, image_file=filename,
                  recipe_distribute=self.distAct.isChecked())

    def run(self):
        self.w.show()
        sys.exit(self.exec_())
