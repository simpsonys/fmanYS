from fbs_runtime.application_context import is_frozen
from fbs_runtime.excepthook import ExceptionHandler
from fman.impl.theme import ThemeError
from fman.impl.util import is_below_dir
from os.path import dirname, basename
from traceback import StackSummary, extract_tb, format_exception, print_exception

import fman
import sys

class PluginErrorHandler(ExceptionHandler):
	def __init__(self, app):
		self._app = app
		self._main_window = None
		self._pending_error_messages = []
		self._plugin_dirs = []
	def add_dir(self, plugin_dir):
		self._plugin_dirs.append(plugin_dir)
	def remove_dir(self, plugin_dir):
		self._plugin_dirs.remove(plugin_dir)
	def handle(self, exc_type, exc_value, enriched_tb):
		causing_plugin = self._get_plugin_causing_error(enriched_tb)
		if causing_plugin and basename(causing_plugin) != 'Core':
			self.report('Plugin %r raised an error.' % basename(causing_plugin))
			return True
	def _get_plugin_causing_error(self, traceback):
		for frame in extract_tb(traceback):
			for plugin_dir in self._plugin_dirs:
				if is_below_dir(frame.filename, plugin_dir):
					return plugin_dir
	def report(self, message, exc=None):
		if exc is None:
			exc = sys.exc_info()[1]
		if exc:
			if not is_frozen():
				# The steps further below only show a pruned stack trace. During
				# development, it's useful if we also see the full stack trace:
				print_exception(type(exc), exc, exc.__traceback__)
			message += '\n\n' + self._get_plugin_traceback(exc)
		if self._main_window:
			self._main_window.show_alert(message)
		else:
			self._pending_error_messages.append(message)
	def handle_system_exit(self, code=0):
		self._app.exit(code)
	def on_main_window_shown(self, main_window):
		self._main_window = main_window
		if self._pending_error_messages:
			self._main_window.show_alert(self._pending_error_messages[0])
	def _get_plugin_traceback(self, exc):
		if isinstance(exc, ThemeError):
			return exc.description
		return format_traceback(exc, exclude_dirs=[dirname(fman.__file__)])

def format_traceback(exc, exclude_dirs):
	def should_include(tb):
		filename = tb.tb_frame.f_code.co_filename
		for dir_ in exclude_dirs:
			if is_below_dir(filename, dir_):
				return False
		return True
	frames = StackSummary.extract(
		_walk_tb_filtered(exc.__traceback__, should_include), lookup_lines=True
	)
	lines = ['Traceback (most recent call last):\n']
	lines.extend(frames.format())
	try:
		exc_str = str(exc)
	except Exception:
		exc_str = '<unprintable %s object>' % type(exc).__name__
	lines.append('%s: %s\n' % (type(exc).__name__, exc_str))
	return ''.join(lines)

def _walk_tb_filtered(tb, tb_filter=None):
	while tb is not None:
		if tb_filter is None or tb_filter(tb):
			yield tb.tb_frame, tb.tb_lineno
		tb = tb.tb_next