import os
import sys
from fman import (
    DirectoryPaneCommand, DirectoryPaneListener,
    _get_app_ctxt, run_application_command
)
from fman.impl.util.qt.thread import run_in_main_thread
from fman.url import as_url
from PyQt5.QtCore import QEvent, QObject, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout, QVBoxLayout,
    QPushButton, QWidget, QSizePolicy, QLabel
)


# =============================================================================
# 1. Drive Navigation
# =============================================================================

class GoToDrive(DirectoryPaneCommand):
    def __call__(self, drive='C'):
        drive = drive.upper()
        local_path = drive + ':\\'
        if os.path.exists(local_path):
            self.pane.set_path(as_url(local_path))


# =============================================================================
# 2. Copy / Move between Panes (directional)
# =============================================================================

class CopyToRightPane(DirectoryPaneCommand):
    def __call__(self):
        panes = self.pane.window.get_panes()
        if len(panes) >= 2 and panes.index(self.pane) == 0:
            self.pane.run_command('copy')

class CopyToLeftPane(DirectoryPaneCommand):
    def __call__(self):
        panes = self.pane.window.get_panes()
        if len(panes) >= 2 and panes.index(self.pane) == 1:
            self.pane.run_command('copy')

class MoveToRightPane(DirectoryPaneCommand):
    def __call__(self):
        panes = self.pane.window.get_panes()
        if len(panes) >= 2 and panes.index(self.pane) == 0:
            self.pane.run_command('move')

class MoveToLeftPane(DirectoryPaneCommand):
    def __call__(self):
        panes = self.pane.window.get_panes()
        if len(panes) >= 2 and panes.index(self.pane) == 1:
            self.pane.run_command('move')


# =============================================================================
# 3. GoTo Current Directory
# =============================================================================

class GoToCurrentDirectory(DirectoryPaneCommand):
    """Open GoTo quicksearch pre-filled with the current directory path."""
    def __call__(self):
        from fman.url import as_human_readable
        path = as_human_readable(self.pane.get_path())
        if not path.endswith(os.sep):
            path += os.sep
        self.pane.run_command('go_to', {'query': path})


# =============================================================================
# 4. Windows dark title bar
# =============================================================================

def _apply_dark_titlebar(hwnd):
    try:
        import ctypes
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value), ctypes.sizeof(value)
        )
    except Exception:
        pass


class DarkTitleBarFilter(QObject):
    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Show
                and isinstance(obj, QWidget)
                and obj.isWindow()
                and obj.parent() is None):
            hwnd = int(obj.winId())
            if hwnd:
                _apply_dark_titlebar(hwnd)
        return False


# =============================================================================
# 4. Dynamic Action Bar
# =============================================================================

# Each entry: (label, 'pane'|'app', command_name, args_dict)
BUTTON_GROUPS = {
    'default': [
        ('[F3] GoTo Current', 'pane', 'go_to_current_directory', {}),
        ('[F2] Rename',       'pane', 'rename',                   {}),
        ('[F6] New File',     'pane', 'create_and_edit_file',     {}),
        ('[F7] New Folder',   'pane', 'create_directory',         {}),
        ('[F8] Flat View',    'pane', 'flat_view',                {}),
        ('[F9] Terminal',     'pane', 'open_terminal',            {}),
        ('[F10] Explorer',    'pane', 'open_native_file_manager', {}),
        ('[F11] Copy Path',   'pane', 'copy_paths_to_clipboard',  {}),
    ],
    'ctrl': [
        ('[C] C Drive',  'pane', 'go_to_drive',        {'drive': 'C'}),
        ('[D] D Drive',  'pane', 'go_to_drive',        {'drive': 'D'}),
        ('[E] E Drive',  'pane', 'go_to_drive',        {'drive': 'E'}),
        ('[→] Copy →',   'pane', 'copy_to_right_pane', {}),
        ('[←] ← Copy',  'pane', 'copy_to_left_pane',  {}),
    ],
    'ctrl_shift': [
        ('[P] Palette',    'app',  'command_palette',      {}),
        ('[F4] New File',  'pane', 'create_and_edit_file', {}),
        ('[F5] Symlink',   'pane', 'symlink',              {}),
        ('[F6] Rename',    'pane', 'rename',               {}),
        ('[Del] Perm Del', 'pane', 'delete_permanently',   {}),
    ],
    'alt': [
        ('[←] ← Move',   'pane', 'move_to_left_pane',        {}),
        ('[→] Move →',    'pane', 'move_to_right_pane',       {}),
        ('[↑] Go Up',     'pane', 'go_up',                    {}),
        ('[Enter] Props', 'pane', 'show_explorer_properties', {}),
        ('[F5] Pack',     'pane', 'pack',                     {}),
    ],
}

BTN_HEIGHT = 22
BAR_HEIGHT = BTN_HEIGHT + 4


class ModifierFilter(QObject):
    state_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._ctrl = False
        self._shift = False
        self._alt = False

    def eventFilter(self, obj, event):
        t = event.type()
        if t in (QEvent.KeyPress, QEvent.KeyRelease):
            key = event.key()
            pressed = (t == QEvent.KeyPress)
            changed = False
            if key == Qt.Key_Control:
                if self._ctrl != pressed:
                    self._ctrl = pressed
                    changed = True
            elif key == Qt.Key_Shift:
                if self._shift != pressed:
                    self._shift = pressed
                    changed = True
            elif key == Qt.Key_Alt:
                if self._alt != pressed:
                    self._alt = pressed
                    changed = True
            if changed:
                self._emit()
        return False

    def _emit(self):
        if self._ctrl and self._shift:
            self.state_changed.emit('ctrl_shift')
        elif self._ctrl:
            self.state_changed.emit('ctrl')
        elif self._alt:
            self.state_changed.emit('alt')
        else:
            self.state_changed.emit('default')


class FocusFilter(QObject):
    focused = pyqtSignal(object)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.focused.emit(obj)
        return False


class ActionBar(QWidget):
    def __init__(self, parent, modifier_filter):
        super().__init__(parent)
        self._pane = None
        self._hlayout = QHBoxLayout()
        self._hlayout.setContentsMargins(1, 1, 1, 1)
        self._hlayout.setSpacing(1)
        self.setLayout(self._hlayout)
        self.setFixedHeight(BAR_HEIGHT)
        modifier_filter.state_changed.connect(self._rebuild)
        self._rebuild('default')

    def set_pane(self, pane):
        self._pane = pane

    def _rebuild(self, state):
        while self._hlayout.count():
            item = self._hlayout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for label, kind, command, args in BUTTON_GROUPS.get(state, []):
            btn = QPushButton(label)
            btn.setFixedHeight(BTN_HEIGHT)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(
                lambda _, k=kind, c=command, a=args: self._run(k, c, a)
            )
            self._hlayout.addWidget(btn)

    def _run(self, kind, command, args):
        try:
            if kind == 'app':
                run_application_command(command, args=args)
            elif self._pane:
                self._pane.run_command(command, args=args)
        except Exception:
            pass


class ActionBarContainer(QWidget):
    def __init__(self, parent, splitter):
        super().__init__(parent)
        self._panes = []

        self._modifier_filter = ModifierFilter()
        QApplication.instance().installEventFilter(self._modifier_filter)

        self._focus_filter = FocusFilter()
        self._focus_filter.focused.connect(self._on_focus)

        self._dark_filter = DarkTitleBarFilter()
        QApplication.instance().installEventFilter(self._dark_filter)

        self._action_bar = ActionBar(self, self._modifier_filter)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(splitter)
        layout.addWidget(self._action_bar)
        self.setLayout(layout)

    def add_pane(self, pane):
        self._panes.append(pane)
        pane._widget._file_view.installEventFilter(self._focus_filter)
        if len(self._panes) == 1:
            self._action_bar.set_pane(pane)

    def _on_focus(self, widget):
        for pane in self._panes:
            if pane._widget._file_view == widget:
                self._action_bar.set_pane(pane)
                return


class PaneTracker(DirectoryPaneListener):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        if _container:
            _container.add_pane(self.pane)


_container = None


def _get_version():
    """Read version from build_tag.txt (CI-generated) or fall back to fman version."""
    try:
        path = _get_app_ctxt().get_resource('build_tag.txt')
        with open(path) as f:
            return f.read().strip()
    except Exception:
        pass
    try:
        import fman
        return 'v' + str(getattr(fman, 'FMAN_VERSION', 'dev'))
    except Exception:
        return 'dev'


@run_in_main_thread
def _init():
    global _container
    window = _get_app_ctxt().main_window
    _container = ActionBarContainer(window, window._splitter)
    window.setCentralWidget(_container)

    # Apply dark title bar to main window
    _apply_dark_titlebar(int(window.winId()))

    # Show version in bottom-right of status bar
    version = _get_version()
    ver_label = QLabel('  ' + version + '  ')
    ver_label.setStyleSheet('color: #6272a4; font-size: 9pt;')
    window.statusBar().addPermanentWidget(ver_label)


_init()
