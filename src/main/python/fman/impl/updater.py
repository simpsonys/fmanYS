from os.path import join, pardir, dirname

import sys

class MacUpdater:
	def __init__(self, app):
		self.app = app
		self._objc_namespace = dict()
		self._sparkle = None
	def start(self):
		from objc import pathForFramework, loadBundle
		frameworks_dir = join(dirname(sys.executable), pardir, 'Frameworks')
		fmwk_path = pathForFramework(join(frameworks_dir, 'Sparkle.framework'))
		loadBundle('Sparkle', self._objc_namespace, bundle_path=fmwk_path)
		self.app.aboutToQuit.connect(self._about_to_quit)
		SUUpdater = self._objc_namespace['SUUpdater']
		self._sparkle = SUUpdater.sharedUpdater()
		self._sparkle.setAutomaticallyChecksForUpdates_(True)
		self._sparkle.setAutomaticallyDownloadsUpdates_(True)
		self._sparkle.checkForUpdatesInBackground()
	def _about_to_quit(self):
		if self._sparkle.updateInProgress():
			# Installing the update takes quite some time. Hide the dock icon so
			# the user doesn't think fman froze:
			self._hide_dock_window()
		self._notify_sparkle_of_app_shutdown()
	def _hide_dock_window(self):
		NSApplication = self._objc_namespace['NSApplication']
		app = NSApplication.sharedApplication()
		app.setActivationPolicy_(NSApplicationActivationPolicyProhibited)
	def _notify_sparkle_of_app_shutdown(self):
		# Qt apps don't receive the NSApplicationWillTerminateNotification
		# event, which Sparkle relies on. If we broadcast the event manually
		# (via NSNotificationCenter.defaultCenter().postNotificationName(...)),
		# then Sparkle does receive it, however during the update process the
		# event is broadcast again, resulting in a second (failing) run of
		# Sparkle's Autoupdate app - see [1] for more information on the issue.
		# The clean way to have the notification broadcast only once is to call
		# Cocoa's terminate(...) method.
		# [1]: https://github.com/sparkle-project/Sparkle/issues/839
		NSApplication = self._objc_namespace['NSApplication']
		NSApplication.sharedApplication().terminate_(None)

NSApplicationActivationPolicyProhibited = 2

class _UpdateSignaller:
	"""Helper to emit a signal from a background thread to the main thread."""
	def __init__(self):
		from PyQt5.QtCore import QObject, pyqtSignal
		class _Signals(QObject):
			found = pyqtSignal(str, str)  # (tag, download_url)
		self._obj = _Signals()
		self.found = self._obj.found

class WindowsUpdater:
	RELEASES_API = 'https://api.github.com/repos/simpsonys/fmanYS/releases'

	def __init__(self, app, current_tag):
		self._app = app
		self._current_tag = (current_tag or '').strip()
		self._signaller = _UpdateSignaller()
		self._signaller.found.connect(self._on_update_found)

	def start(self):
		from threading import Thread
		Thread(target=self._check, daemon=True).start()

	def _check(self):
		try:
			import requests
			resp = requests.get(self.RELEASES_API, timeout=10)
			releases = resp.json()
			if not isinstance(releases, list) or not releases:
				return
			latest = releases[0]
			tag = latest.get('tag_name', '')
			if not tag or tag == self._current_tag:
				return
			url = self._find_asset_url(latest, 'portable')
			if not url:
				url = self._find_asset_url(latest, 'setup')
			self._signaller.found.emit(tag, url)
		except Exception:
			pass

	def _find_asset_url(self, release, keyword):
		for asset in release.get('assets', []):
			if keyword.lower() in asset.get('name', '').lower():
				return asset['browser_download_url']
		return ''

	def _on_update_found(self, tag, url):
		from PyQt5.QtWidgets import QMessageBox
		reply = QMessageBox.question(
			None, 'fmanYS 업데이트',
			f'새 버전이 있습니다: {tag}\n지금 업데이트 하시겠습니까?',
			QMessageBox.Yes | QMessageBox.No,
			QMessageBox.Yes
		)
		if reply == QMessageBox.Yes:
			self._download_and_apply(url, tag)

	def _download_and_apply(self, url, tag):
		import os
		import tempfile
		from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication
		from PyQt5.QtCore import Qt

		if not url:
			QMessageBox.information(
				None, 'fmanYS 업데이트',
				f'다운로드 링크를 찾을 수 없습니다.\n'
				f'https://github.com/simpsonys/fmanYS/releases 에서 직접 다운로드하세요.'
			)
			return

		dlg = QProgressDialog('업데이트 다운로드 중...', '취소', 0, 100)
		dlg.setWindowTitle('fmanYS 업데이트')
		dlg.setWindowModality(Qt.WindowModal)
		dlg.setMinimumDuration(0)
		dlg.setValue(0)
		dlg.show()
		QApplication.processEvents()

		try:
			import requests
			resp = requests.get(url, stream=True, timeout=120)
			total = int(resp.headers.get('content-length', 0))
			suffix = '.exe'
			fd, tmp_path = tempfile.mkstemp(suffix=suffix)
			downloaded = 0
			with os.fdopen(fd, 'wb') as f:
				for chunk in resp.iter_content(chunk_size=65536):
					if dlg.wasCanceled():
						os.unlink(tmp_path)
						return
					f.write(chunk)
					downloaded += len(chunk)
					if total:
						dlg.setValue(int(downloaded * 100 / total))
					QApplication.processEvents()
			dlg.close()

			exe_path = sys.executable
			is_portable = 'portable' in os.path.basename(exe_path).lower()
			if is_portable:
				self._swap_portable(tmp_path, exe_path)
			else:
				import subprocess
				subprocess.Popen([tmp_path])
				self._app.quit()
		except Exception as e:
			dlg.close()
			QMessageBox.critical(None, '업데이트 실패', str(e))

	def _swap_portable(self, new_exe, current_exe):
		import os
		import subprocess
		import tempfile
		bat = (
			'@echo off\n'
			'timeout /t 2 /nobreak >NUL\n'
			f'move /y "{new_exe}" "{current_exe}"\n'
			f'start "" "{current_exe}"\n'
			'del "%~f0"\n'
		)
		fd, bat_path = tempfile.mkstemp(suffix='.bat')
		with os.fdopen(fd, 'w') as f:
			f.write(bat)
		subprocess.Popen(
			['cmd', '/c', bat_path],
			creationflags=subprocess.CREATE_NO_WINDOW
		)
		self._app.quit()
