from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QTreeView, QMenu, QAction

from networkitem import NetworkItem


class NetworkView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)

    def disable_item_action(self):
        indexes = self.selectionModel().selection().indexes()
        for index in indexes:
            item = self.model().itemFromIndex(index)
            item.disable()

    def enable_item_action(self):
        indexes = self.selectionModel().selection().indexes()
        for index in indexes:
            item = self.model().itemFromIndex(index)
            item.enable()

    def copy_item_action(self):
        indexes = self.selectionModel().selection().indexes()
        for index in indexes:
            item = self.model().itemFromIndex(index)
            newItem = NetworkItem(item.network().copy())
            self.model().invisibleRootItem().appendRow(newItem)

    def delete_item_action(self):
        indexes = self.selectionModel().selection().indexes()
        for index in indexes:
            item = self.model().itemFromIndex(index)
            if type(item) == NetworkItem:
                self.model().removeRow(index.row(), index.parent())
            else:
                parentIdx = self.model().indexFromItem(item.parent())
                self.model().removeRow(parentIdx.row(),parentIdx.parent())

    def contextMenuEvent(self, event: QContextMenuEvent):
        # Create the context menu
        menu = QMenu(self)

        # Create actions for the menu
        action_disable = QAction("Hide", self)
        action_enable = QAction("Show", self)
        action_copy = QAction("Copy", self)
        action_delete = QAction("Delete", self)

        # Connect the actions to their respective slots
        action_disable.triggered.connect(self.disable_item_action)
        action_enable.triggered.connect(self.enable_item_action)
        action_copy.triggered.connect(self.copy_item_action)
        action_delete.triggered.connect(self.delete_item_action)

        # Add the actions to the menu
        menu.addAction(action_disable)
        menu.addAction(action_enable)
        menu.addSeparator()
        menu.addAction(action_copy)
        menu.addAction(action_delete)

        # Show the context menu at the event's position
        menu.popup(event.globalPos())

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == Qt.Key_D:
            self.disable_item_action()
        elif event.key() == Qt.Key_E:
            self.enable_item_action()
        elif event.key() == Qt.Key_Delete:
            self.delete_item_action()
        else:
            pass


