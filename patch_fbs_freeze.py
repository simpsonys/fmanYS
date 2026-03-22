"""
Patch fbs.freeze.windows to skip the msvcr100.dll check.
This DLL check is not needed when using PyInstaller 6.x.
"""
import fbs.freeze.windows as m
import inspect

path = inspect.getfile(m)
with open(path, encoding='utf-8') as f:
    src = f.read()

if '_add_missing_dlls()' in src:
    src = src.replace('_add_missing_dlls()', 'pass  # skipped: msvcr100.dll not required')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(src)
    print('Patched:', path)
else:
    print('Already patched or not found:', path)
