"""
Runtime hook for --onefile portable build.

1. Patches fbs_runtime._frozen.get_resource_dirs so bundled resources
   in sys._MEIPASS are found.
2. Patches fman.impl.plugins.discover.find_plugin_dirs so that
   Third-party and User plugins bundled inside the exe are loaded.
   Bundled plugins are MERGED with AppData plugins (not replaced), so
   user-installed plugins remain available even in partial CI builds.
"""
import sys
import os

# ---------------------------------------------------------------------------
# 1. Resource dir patch (original behaviour)
# ---------------------------------------------------------------------------
_orig_get_resource_dirs = None

def _patched_get_resource_dirs():
    dirs = _orig_get_resource_dirs()
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass and meipass not in dirs:
        dirs = [meipass] + dirs
    return dirs

import fbs_runtime._frozen as _frozen
_orig_get_resource_dirs = _frozen.get_resource_dirs
_frozen.get_resource_dirs = _patched_get_resource_dirs

# ---------------------------------------------------------------------------
# 2. Plugin discovery patch — MERGE bundled plugins with AppData plugins
# ---------------------------------------------------------------------------
import fman.impl.plugins.discover as _discover

_orig_find_plugin_dirs = _discover.find_plugin_dirs

def _patched_find_plugin_dirs(shipped_plugins, thirdparty_plugins, user_plugins):
    meipass = getattr(sys, '_MEIPASS', None)
    # Start with the AppData-based result (preserves user-installed plugins)
    result = _orig_find_plugin_dirs(shipped_plugins, thirdparty_plugins, user_plugins)
    if not meipass:
        return result
    # Settings plugin is always the last element; insert before it
    existing_names = {os.path.basename(p) for p in result}
    for subdir in ('Third-party', 'User'):
        bundled_dir = os.path.join(meipass, 'Plugins', subdir)
        if not os.path.isdir(bundled_dir):
            continue
        for name in sorted(os.listdir(bundled_dir)):
            full = os.path.join(bundled_dir, name)
            if os.path.isdir(full) and name not in existing_names:
                existing_names.add(name)
                result.insert(-1, full)  # before Settings (always last)
    return result

_discover.find_plugin_dirs = _patched_find_plugin_dirs
