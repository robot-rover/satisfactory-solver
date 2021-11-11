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
        self.setWindowTitle('Recipe Viewer')
        self.resize(300, 500)
        self.layout = qtw.QHBoxLayout()
        self.setLayout(self.layout)

        recipes = [
            recipe for recipe in game_data.recipes.values()
            if any(output == item.id for output in recipe.outputs)
            or any(input == item.id for input in recipe.inputs)
        ]

        self.recipe_view = qtw.QListView()
        self.layout.addWidget(self.recipe_view)

        self.recipe_model = ListModel(recipes)
        self.recipe_view.setModel(self.recipe_model)
