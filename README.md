# fmanYS

A customized dual-pane file manager based on [fman](https://fman.io), optimized for power users on Windows.

---

## Keyboard Shortcuts

### Function Keys (default state)

| Key | Action |
|-----|--------|
| `F2` | Rename file/folder |
| `F3` | GoTo — open navigation dialog pre-filled with current directory |
| `F4` | Edit file in default editor |
| `F5` | Open current folder in VS Code |
| `F6` | Create new file (and open in editor) |
| `F7` | Create new folder |
| `F8` | Flat View — list all files recursively in current folder |
| `F9` | Open terminal in current folder |
| `F10` | Open current folder in Windows Explorer |
| `F11` | Copy file path(s) to clipboard |

### Ctrl + Key

| Key | Action |
|-----|--------|
| `Ctrl+Right` | Copy selected files to right pane |
| `Ctrl+Left` | Copy selected files to left pane |
| `Ctrl+T` | **Tree View** — run `tree /a` on current folder; shows prompt to edit command before running, output opens in editor |
| `Ctrl+L` | **File List** — run `dir /s /o /b` on current folder; shows prompt to edit command before running, output opens in editor |

### Ctrl+Shift + Key (action bar shown when Ctrl+Shift held)

| Key | Action |
|-----|--------|
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+Shift+F4` | Create new file |
| `Ctrl+Shift+F5` | Create symbolic link |
| `Ctrl+Shift+F6` | Rename |
| `Ctrl+Shift+Del` | Permanently delete (bypass Recycle Bin) |

### Alt + Key

| Key | Action |
|-----|--------|
| `Alt+C` | Navigate to C:\ |
| `Alt+D` | Navigate to D:\ |
| `Alt+E` | Navigate to E:\ |
| `Alt+Right` | Move selected files to right pane |
| `Alt+Left` | Move selected files to left pane |
| `Alt+Up` | Go up one directory level |
| `Alt+Enter` | Show file/folder properties (Windows Explorer) |
| `Alt+F5` | Pack (create archive) |

### Arrow Key Navigation

| Key | Action |
|-----|--------|
| `Left Arrow` | Go up one directory level |
| `Right Arrow` | Open directory (or file) |

---

## Features

### Dynamic Action Bar
A button bar at the bottom of the window changes based on which modifier keys are held:
- **No modifier** — function key shortcuts (F2–F11)
- **Ctrl** — copy operations + Tree View / File List
- **Ctrl+Shift** — power operations (palette, symlink, permanent delete)
- **Alt** — drive navigation + move operations

### Tree View (`Ctrl+T`)
Opens a prompt pre-filled with `tree /a "<current path>"`. You can modify the command (e.g. add `/f` to include files, change depth) and press Enter. The output is written to a temp file and opened in the system's default text editor.

### File List (`Ctrl+L`)
Opens a prompt pre-filled with `dir /s /o /b "<current path>"`. Modify the options as needed and press Enter. Output opens in the default text editor.

### GoTo Current Directory (`F3`)
Opens fman's GoTo dialog pre-filled with the current pane's path, so you can quickly type a subdirectory or a new path without retyping the base.

### Dark Title Bar
Automatically applies Windows 11/10 immersive dark mode to the title bar.

### Version Display
The build version is shown in the bottom-right corner of the status bar in white.

---

## Bundled Plugins

The following plugins are bundled in the build:

| Plugin | Description |
|--------|-------------|
| **YSCommands** | Custom shortcuts, action bar, Tree View, File List, version display |
| **FmanAlternativeColors** | Color themes (Dracula, Material Dark, Nord, etc.) |
| **FmanBookmarks** | Bookmark directories for quick navigation |
| **FmanDotEntries** | Show/hide hidden (dot) files |
| **ArrowNavigation** | Navigate with left/right arrow keys |
| **GoToSameDirectoryInOtherPane** | Mirror current directory to the other pane |
| **OpenFolderInVSCode** | Open folder in VS Code (`F5`) |
| **fman-flatview** | Recursive flat view of all files (`F8`) |
| **fman-fuzzy-search-files** | Fuzzy search files in all subdirectories |
| **FuzzySearchFilesInCurrentFolder** | Fuzzy search within current folder only |
| **StatusBarExtended** | Extended status bar with file size info |
| **Preview** | File preview pane |
| **fman_unzip** | Unzip archives in-place |

---

## Development

Requires Python 3.9.

```
pip install -Ur requirements/windows.txt
python build.py run          # Run in development
python build.py freeze       # Create standalone build
python build.py installer    # Create installer
python build_portable.py     # Create single-file portable exe
```

The portable build automatically includes all plugins from:
- `src/main/resources/base/Plugins/` (bundled with the repo)
- `%APPDATA%\fman\Plugins\Third-party\` (locally installed)
- `%APPDATA%\fman\Plugins\User\` (user settings)
