import PySide6.QtWidgets as qtw
import PySide6.QtCore as qtc
import PySide6.QtGui as qtg


class ListModel(qtc.QAbstractListModel):
    def __init__(self, recipes):
        super().__init__()
        self.recipes = recipes

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
    def __init__(self, item, game_data):
        super().__init__()
        self.setWindowTitle(f'Recipe Viewer - {item.display}')
        self.resize(500, 300)
        self.layout = qtw.QHBoxLayout()
        self.setLayout(self.layout)

        self.lists_layout = qtw.QVBoxLayout()
        self.layout.addLayout(self.lists_layout)

        # self.item_label = qtw.QLabel(item.display)
        # font = qtg.QFont(self.item_label.font())
        # font.setPointSize(32)
        # self.item_label.setFont(font)
        # self.lists_layout.addWidget(self.item_label)

        input_recipes = [
            recipe for recipe in game_data.recipes.values()
            if any(input == item.id for input in recipe.inputs)
        ]

        self.input_group = qtw.QGroupBox('Input to')
        self.input_group.setFlat(True)
        self.lists_layout.addWidget(self.input_group)

        self.input_list_layout = qtw.QVBoxLayout()
        self.input_group.setLayout(self.input_list_layout)

        self.input_list = qtw.QListView()
        self.input_model = ListModel(input_recipes)
        self.input_list.setModel(self.input_model)
        self.input_list_layout.addWidget(self.input_list)

        output_recipes = [
            recipe for recipe in game_data.recipes.values()
            if any(output == item.id for output in recipe.outputs)
        ]

        self.output_group = qtw.QGroupBox('Output From')
        self.output_group.setFlat(True)
        self.lists_layout.addWidget(self.output_group)

        self.output_list_layout = qtw.QVBoxLayout()
        self.output_group.setLayout(self.output_list_layout)

        self.output_list = qtw.QListView()
        self.output_model = ListModel(output_recipes)
        self.output_list.setModel(self.output_model)
        self.output_list_layout.addWidget(self.output_list)

    def select_recipe(self, recipe, input):
        if input:
            self.input_list.clearSelection()
        else:
            self.output_list.clearSelection()
        print(recipe.id, recipe.display)

