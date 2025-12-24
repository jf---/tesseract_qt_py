from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget, QToolBar, QMenuBar, QStatusBar
from PySide6.QtGui import QAction, QKeySequence


class StudioMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("MainWindow")
        self.resize(800, 600)

        # Central widget
        self.setCentralWidget(QWidget(self))

        # Create actions
        self._create_actions()

        # Create menus
        self._create_menus()

        # Create toolbar
        self._create_toolbar()

        # Status bar
        self.setStatusBar(QStatusBar(self))

    def _create_actions(self):
        self.action_load_config = QAction("Load Config", self)
        self.action_load_config.setShortcut(QKeySequence("Ctrl+O"))

        self.action_save_config = QAction("Save Config", self)
        self.action_save_config.setShortcut(QKeySequence("Ctrl+S"))
        self.action_save_config.setEnabled(False)

        self.action_save_config_as = QAction("Save Config As", self)
        self.action_save_config_as.setShortcut(QKeySequence("Ctrl+Shift+S"))

        self.action_restore_state = QAction("Restore State", self)
        self.action_save_state = QAction("Save State", self)
        self.action_create_perspective = QAction("Create Perspective", self)
        self.action_load_plugins = QAction("Load Plugins", self)

    def _create_menus(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.action_load_config)
        file_menu.addAction(self.action_save_config)
        file_menu.addAction(self.action_save_config_as)
        file_menu.addSeparator()
        file_menu.addAction(self.action_restore_state)
        file_menu.addAction(self.action_save_state)

        # View menu (empty for dock widgets)
        self.view_menu = menubar.addMenu("View")

        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        tools_menu.addAction(self.action_load_plugins)

    def _create_toolbar(self):
        toolbar = QToolBar(self)
        toolbar.addAction(self.action_restore_state)
        toolbar.addAction(self.action_save_state)
        toolbar.addAction(self.action_create_perspective)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
