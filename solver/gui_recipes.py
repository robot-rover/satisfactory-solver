import os
import yaml

import PySide6.QtWidgets as qtw
import PySide6.QtCore as qtc
from appdirs import user_config_dir

from .config import AlternateRecipeConfiguration


class TreeItem:
    def __init__(self, *args, recipe=None, label=None, checked=False, children=None):
        self.parent = None
        self.row = None
        assert recipe is not None or label is not None
        self.recipe = recipe
        self.label = label
        self.children = []
        self.checked = checked
        if children is not None:
            for child in children:
                self.add_child(child)

    def get_display(self):
        if self.recipe is not None:
            return self.recipe.display
        return self.label

    def add_child(self, child):
        child_row = len(self.children)
        child.parent = self
        child.row = child_row
        self.children.append(child)

    def is_recipe_enabled(self):
        assert self.checked != qtc.Qt.PartiallyChecked, "Inner node is not Recipe"
        return self.checked == qtc.Qt.Checked


class TreeModel(qtc.QAbstractItemModel):
    def __init__(self, tree_root, parent=None):
        super().__init__(parent)
        self.root_item = tree_root
        self.item_lookup = None
        self.create_lookup()
        self.sort()

    def create_lookup(self):
        assert self.item_lookup is None
        self.item_lookup = {}

        def dfs(item):
            if item.recipe is not None:
                self.item_lookup[item.recipe.id] = item
            for child in item.children:
                dfs(child)
        dfs(self.root_item)

    def check_all(self, is_enable):
        set_state = qtc.Qt.Checked if is_enable else qtc.Qt.Unchecked
        for child in self.root_item.children:
            self.dfs(child, set_state)

    def setData(self, index, value, role):
        if role == qtc.Qt.CheckStateRole:
            item = index.internalPointer()
            self.propagate_check(item, value)
            return True
        return False

    def sort(self, item=None):
        if item is None:
            item = self.root_item
        item.children.sort(key=lambda item: item.get_display())
        for index, child in enumerate(item.children):
            child.row = index
            self.sort(child)

    def dfs(self, item, set_state):
        if item.checked != set_state:
            item.checked = set_state
            index = self.createIndex(item.row, 0, item)
            self.dataChanged.emit(index, index, qtc.Qt.CheckStateRole)
            for child in item.children:
                self.dfs(child, set_state)

    def propagate_check(self, item, is_enable):
        set_state = qtc.Qt.Checked if is_enable else qtc.Qt.Unchecked

        def upward(item):
            checked = False
            partially = False
            unchecked = False
            for child in item.children:
                if child.checked == qtc.Qt.Checked:
                    checked = True
                elif child.checked == qtc.Qt.PartiallyChecked:
                    partially = True
                else:
                    unchecked = True
            previous = item.checked
            if partially or (checked and unchecked):
                item.checked = qtc.Qt.PartiallyChecked
            elif checked:
                item.checked = qtc.Qt.Checked
            else:
                item.checked = qtc.Qt.Unchecked
            if previous != item.checked:
                index = self.createIndex(item.row, 0, item)
                self.dataChanged.emit(index, index, qtc.Qt.CheckStateRole)
                if item.parent != self.root_item:
                    upward(item.parent)

        if set_state != item.checked:
            self.dfs(item, set_state)
            if item.parent != self.root_item:
                upward(item.parent)

    def data(self, index, role):
        if not index.isValid():
            return None

        if role == qtc.Qt.DisplayRole:
            item = index.internalPointer()
            return item.get_display()
        elif role == qtc.Qt.CheckStateRole:
            item = index.internalPointer()
            return item.checked
        else:
            return None

    def flags(self, index):
        if not index.isValid():
            return qtc.Qt.NoItemFlags

        return qtc.Qt.ItemIsUserCheckable | qtc.Qt.ItemIsEnabled | qtc.Qt.ItemIsAutoTristate

    def headerData(self, section, orientation, role):
        pass

    def index(self, row, column, parent=qtc.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return qtc.QModelIndex()

        parent_item = self.root_item
        if parent.isValid():
            parent_item = parent.internalPointer()

        child = parent_item.children[row] if row < len(
            parent_item.children) else None
        if child is not None:
            return self.createIndex(row, column, child)
        return qtc.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return qtc.QModelIndex()

        child = index.internalPointer()
        parent = child.parent

        if parent == self.root_item:
            return qtc.QModelIndex()
        return self.createIndex(parent.row, 0, parent)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        parent_item = self.root_item
        if parent.isValid():
            parent_item = parent.internalPointer()

        return len(parent_item.children)

    def columnCount(self, parent):
        return 1


class AlternateRecipeWindow(qtw.QWidget):
    def __init__(self, game_data):
        super().__init__()
        config_dir = user_config_dir(
            'satisfactory-solver', 'robot_rover')
        os.makedirs(config_dir, exist_ok=True)
        self.default_location = os.path.join(
            config_dir, 'default_recipes.yaml')

        self.setWindowTitle('Enabled Recipes')
        self.resize(300, 500)
        self.layout = qtw.QVBoxLayout()
        self.setLayout(self.layout)

        self.button_layout = qtw.QGridLayout()
        self.layout.addLayout(self.button_layout)

        self.all_on_btn = qtw.QPushButton('Enable All')
        self.button_layout.addWidget(self.all_on_btn, 0, 0)
        self.all_off_btn = qtw.QPushButton('Disable All')
        self.button_layout.addWidget(self.all_off_btn, 1, 0)

        self.all_open_btn = qtw.QPushButton('Expand All')
        self.button_layout.addWidget(self.all_open_btn, 0, 1)
        self.all_close_btn = qtw.QPushButton('Collapse All')
        self.button_layout.addWidget(self.all_close_btn, 1, 1)

        self.recipe_view = qtw.QTreeView()
        recipe_root = self.build_tree(game_data)
        self.recipe_model = TreeModel(recipe_root)
        self.recipe_view.setModel(self.recipe_model)
        self.recipe_view.setHeaderHidden(True)
        self.layout.addWidget(self.recipe_view)

        self.bottom_layout = qtw.QGridLayout()
        self.layout.addLayout(self.bottom_layout)

        self.load_btn = qtw.QPushButton('Load Config')
        self.bottom_layout.addWidget(self.load_btn, 0, 0)
        self.save_btn = qtw.QPushButton('Save Config')
        self.bottom_layout.addWidget(self.save_btn, 1, 0)
        self.default_btn = qtw.QPushButton('Set as Default')
        self.bottom_layout.addWidget(self.default_btn, 0, 1)
        self.reload_btn = qtw.QPushButton('Reload Default')
        self.bottom_layout.addWidget(self.reload_btn, 1, 1)

        self.all_on_btn.clicked.connect(
            lambda: self.recipe_model.check_all(True))
        self.all_off_btn.clicked.connect(
            lambda: self.recipe_model.check_all(False))
        self.all_open_btn.clicked.connect(
            self.recipe_view.expandAll
        )
        self.all_close_btn.clicked.connect(
            self.recipe_view.collapseAll
        )

        self.save_btn.clicked.connect(
            self.save_config
        )
        self.load_btn.clicked.connect(
            self.load_config
        )
        self.default_btn.clicked.connect(
            lambda: self.save_config(True)
        )
        self.reload_btn.clicked.connect(
            lambda: self.load_config(True)
        )

        self.load_config(self.default_location)

    def from_recipe_config(self, config):
        self.recipe_model.check_all(False)
        for enabled_recipe_id, enabled in config.enabled_recipes.items():
            if enabled:
                self.recipe_model.propagate_check(
                    self.recipe_model.item_lookup[enabled_recipe_id], True)

    def to_recipe_config(self):
        return AlternateRecipeConfiguration({
            recipe_id: tree_item.is_recipe_enabled() for recipe_id, tree_item in self.recipe_model.item_lookup.items()})

    def get_default_config(self):
        return AlternateRecipeConfiguration({
            recipe_id: True for recipe_id in self.recipe_model.item_lookup
        })

    def save_config(self, default=False):
        config = self.to_recipe_config()
        if len(config.enabled_recipes) == 0:
            qtw.QMessageBox.warning(self, "Select a Recipe!",
                                    "All recipes are currently disabled!")
            return
        if default:
            file_name = self.default_location
        else:
            file_name, file_type = qtw.QFileDialog.getSaveFileName(
                self, "Save Recipe Configuration", 'recipes.yaml', 'Recipe Configuration (*.yaml)')
            if file_name == '':
                return
        print(f'Writing Config to f{file_name}')
        with open(file_name, 'w') as file:
            yaml.dump(config.to_dict(), file)

    def load_config(self, default=False):
        if default:
            file_name = self.default_location
            if not os.path.exists(file_name):
                self.from_recipe_config(self.get_default_config())
                return
        else:
            file_name, file_type = qtw.QFileDialog.getOpenFileName(
                self, 'Load Recipe Configuration', '.', 'Recipe Configuration (*.yaml)'
            )
        if file_name == '':
            return
        with open(file_name, 'r') as file:
            config = AlternateRecipeConfiguration.from_dict(
                yaml.safe_load(file))
        self.from_recipe_config(config)

    def build_tree(self, game_data):
        root = TreeItem(label='Recipes')

        def get_or_insert(item, val):
            for child in item.children:
                if child.label == val:
                    return child
            new = TreeItem(label=val)
            item.add_child(new)
            return new

        for recipe in game_data.recipes.values():
            parent = root
            for unlock_step in recipe.unlock:
                parent = get_or_insert(parent, unlock_step)
            parent.add_child(TreeItem(recipe=recipe))

        return root
