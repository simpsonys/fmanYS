"""
Runtime hook for --onefile portable build.

1. Patches fbs_runtime._frozen.get_resource_dirs so bundled resources
   in sys._MEIPASS are found.
2. Patches fman.impl.plugins.discover.find_plugin_dirs so that
   Third-party and User plugins bundled inside the exe are loaded.
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
# 2. Plugin discovery patch — include bundled Third-party and User plugins
# ---------------------------------------------------------------------------
import fman.impl.plugins.discover as _discover

_orig_find_plugin_dirs = _discover.find_plugin_dirs

def _patched_find_plugin_dirs(shipped_plugins, thirdparty_plugins, user_plugins):
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        bundled_thirdparty = os.path.join(meipass, 'Plugins', 'Third-party')
        bundled_user = os.path.join(meipass, 'Plugins', 'User')
        if os.path.isdir(bundled_thirdparty):
            thirdparty_plugins = bundled_thirdparty
        if os.path.isdir(bundled_user):
            user_plugins = bundled_user
    return _orig_find_plugin_dirs(shipped_plugins, thirdparty_plugins, user_plugins)

_discover.find_plugin_dirs = _patched_find_plugin_dirs
