from PyQt5.QtWidgets import QTreeView, QMenu, QAction


class NetworkView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)

    def contextMenuEvent(self, event):
        # Create the context menu
        menu = QMenu(self)

        # Create actions for the menu
        action1 = QAction("Disable", self)
        action2 = QAction("Delete", self)

        # Connect the actions to their respective slots
        action1.triggered.connect(self.on_action1_triggered)
        action2.triggered.connect(self.on_action2_triggered)

        # Add the actions to the menu
        menu.addAction(action1)
        menu.addAction(action2)

        # Show the context menu at the event's position
        menu.popup(event.globalPos())

        def on_action1_triggered(self):
            print("Action 1 triggered!")

        def on_action2_triggered(self):
            print("Action 2 triggered!")
