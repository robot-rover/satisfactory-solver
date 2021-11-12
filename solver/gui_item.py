import itertools

import PySide6.QtWidgets as qtw
import PySide6.QtCore as qtc
import PySide6.QtGui as qtg

from .util import clearLayout


class ListModel(qtc.QAbstractListModel):
    def __init__(self, recipes=[]):
        super().__init__()
        self.recipes = recipes

    def set_recipes(self, recipes):
        self.beginRemoveRows(self.createIndex(
            0, 0, None), 0, len(self.recipes) - 1)
        self.recipes = []
        self.endRemoveRows()

        self.beginInsertRows(self.createIndex(0, 0, None), 0, len(recipes) - 1)
        self.recipes = recipes
        self.endInsertRows()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role == qtc.Qt.DisplayRole:
            return self.recipes[index.row()].display
        else:
            return None

    def flags(self, index):
        if not index.isValid():
            return qtc.Qt.NoItemFlags

        return qtc.Qt.ItemIsEnabled

    def rowCount(self, parent):
        return len(self.recipes)

    def columnCount(self, parent):
        return 1


class RecipeListWindow(qtw.QWidget):
    def __init__(self, item, game_data, open_recipe_window):
        super().__init__()
        self.game_data = game_data

        self.resize(700, 400)
        self.layout = qtw.QHBoxLayout()
        self.layout.setSpacing(20)
        self.setLayout(self.layout)

        self.lists_layout = qtw.QVBoxLayout()
        self.layout.addLayout(self.lists_layout)

        self.input_group = qtw.QGroupBox('Input to')
        self.input_group.setFlat(True)
        self.lists_layout.addWidget(self.input_group)

        self.input_list_layout = qtw.QVBoxLayout()
        self.input_group.setLayout(self.input_list_layout)

        self.input_list = qtw.QListView()
        self.input_model = ListModel()
        self.input_list.setModel(self.input_model)
        self.input_list.clicked.connect(
            lambda index: self.select_recipe(index, True))
        self.input_list_layout.addWidget(self.input_list)

        self.output_group = qtw.QGroupBox('Output From')
        self.output_group.setFlat(True)
        self.lists_layout.addWidget(self.output_group)

        self.output_list_layout = qtw.QVBoxLayout()
        self.output_group.setLayout(self.output_list_layout)

        self.output_list = qtw.QListView()
        self.output_model = ListModel()
        self.output_list.setModel(self.output_model)
        self.output_list.clicked.connect(
            lambda index: self.select_recipe(index, False))
        self.output_list_layout.addWidget(self.output_list)

        self.recipe_layout = qtw.QVBoxLayout()
        self.layout.addLayout(self.recipe_layout, 1)

        self.machine_layout = qtw.QHBoxLayout()
        self.recipe_layout.addLayout(self.machine_layout)

        self.machine_icon = qtw.QLabel()
        self.machine_icon.setMinimumSize(100, 100)
        self.machine_icon.setAlignment(qtc.Qt.AlignRight)
        self.machine_layout.addWidget(self.machine_icon)

        self.machine_name = qtw.QLabel()
        self.machine_layout.addWidget(self.machine_name)

        self.recipe_flow = qtw.QHBoxLayout()
        self.recipe_layout.addLayout(self.recipe_flow, 1)

        self.input_flow_group = qtw.QGroupBox('Inputs')
        self.recipe_flow.addWidget(self.input_flow_group, 1)
        self.input_flow = qtw.QVBoxLayout()
        self.input_flow_group.setLayout(self.input_flow)

        self.output_flow_group = qtw.QGroupBox('Outputs')
        self.recipe_flow.addWidget(self.output_flow_group, 1)
        self.output_flow = qtw.QVBoxLayout()
        self.output_flow_group.setLayout(self.output_flow)

        self.select_item(item)

    def create_flow_item(self, item_id, rate):
        item = self.game_data.items[item_id]
        # label = qtw.QLabel(f'{item.display} x {rate}')
        layout = qtw.QHBoxLayout()

        item_icon = qtw.QPushButton()
        item_icon.setFlat(True)
        item_icon.setFixedSize(50, 50)
        item_icon.clicked.connect(lambda: self.select_item(item))
        pixmap = qtg.QPixmap(item.icon).scaledToHeight(
            50, qtc.Qt.SmoothTransformation)
        icon = qtg.QIcon(pixmap)
        item_icon.setIcon(icon)
        item_icon.setIconSize(pixmap.rect().size())
        layout.addWidget(item_icon)

        item_label = qtw.QLabel(f'{item.display}\nx{rate}')
        layout.addWidget(item_label, 1)
        return layout

    def clear_recipe(self):
        self.machine_name.clear()
        self.machine_icon.clear()
        while self.input_flow.count() > 0:
            clearLayout(self.input_flow.takeAt(0).layout())

        while self.output_flow.count() > 0:
            clearLayout(self.output_flow.takeAt(0).layout())

    def select_item(self, item):
        self.clear_recipe()
        self.setWindowTitle(f'Recipe Viewer - {item.display}')

        input_recipes = [
            recipe for recipe in self.game_data.recipes.values()
            if any(input == item.id for input in recipe.inputs)
        ]
        self.input_model.set_recipes(input_recipes)

        output_recipes = [
            recipe for recipe in self.game_data.recipes.values()
            if any(output == item.id for output in recipe.outputs)
        ]
        self.output_model.set_recipes(output_recipes)

    def select_recipe(self, index, is_input):
        self.clear_recipe()
        if is_input:
            recipe = self.input_model.recipes[index.row()]
        else:
            recipe = self.output_model.recipes[index.row()]
        machine = self.game_data.machines[recipe.machine]
        per_min = round(1/recipe.duration, 3)
        self.machine_name.setText(
            f'{machine.display}\n{per_min} / min\n{machine.power} MW')
        pixmap = qtg.QPixmap(machine.icon).scaledToHeight(
            100, qtc.Qt.SmoothTransformation)
        self.machine_icon.setPixmap(pixmap)

        for item_id, rate in recipe.inputs.items():
            self.input_flow.addLayout(self.create_flow_item(item_id, rate))

        for item_id, rate in recipe.outputs.items():
            self.output_flow.addLayout(self.create_flow_item(item_id, rate))
