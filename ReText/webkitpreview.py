# vim: ts=8:sts=8:sw=8:noexpandtab
#
# This file is part of ReText
# Copyright: 2015-2021 Dmitry Shachnev
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from ReText import globalSettings
from ReText.syncscroll import SyncScroll
from ReText.preview import ReTextWebPreview

from PyQt6.QtCore import QStandardPaths
from PyQt6.QtGui import QDesktopServices, QTextDocument
from PyQt6.QtNetwork import QNetworkDiskCache
from PyQt6.QtWebKit import QWebSettings
from PyQt6.QtWebKitWidgets import QWebPage, QWebView


class ReTextWebKitPreview(ReTextWebPreview, QWebView):

	def __init__(self, tab,
	             editorPositionToSourceLineFunc,
	             sourceLineToEditorPositionFunc):

		QWebView.__init__(self)
		self.tab = tab

		self.syncscroll = SyncScroll(self.page().mainFrame(),
		                             editorPositionToSourceLineFunc,
		                             sourceLineToEditorPositionFunc)
		ReTextWebPreview.__init__(self, tab.editBox)

		self.page().setLinkDelegationPolicy(QWebPage.LinkDelegationPolicy.DelegateAllLinks)
		self.page().linkClicked.connect(self._handleLinkClicked)
		self.settings().setAttribute(QWebSettings.WebAttribute.LocalContentCanAccessFileUrls, False)
		# Avoid caching of CSS
		self.settings().setObjectCacheCapacities(0,0,0)

		self.cache = QNetworkDiskCache()
		cacheDirectory = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation)
		self.cache.setCacheDirectory(cacheDirectory)
		self.page().networkAccessManager().setCache(self.cache)

	def updateFontSettings(self):
		settings = self.settings()
		settings.setFontFamily(QWebSettings.FontFamily.StandardFont,
		                       globalSettings.font.family())
		settings.setFontSize(QWebSettings.FontSize.DefaultFontSize,
		                     globalSettings.font.pointSize())

	def _handleWheelEvent(self, event):
		# Only pass wheelEvents on to the preview if syncscroll is
		# controlling the position of the preview
		if self.syncscroll.isActive():
			self.wheelEvent(event)

	def _handleLinkClicked(self, url):
		if url.isLocalFile():
			localFile = url.toLocalFile()
			if localFile == self.tab.fileName and url.hasFragment():
				self.page().mainFrame().scrollToAnchor(url.fragment())
				return
			if self.tab.openSourceFile(localFile):
				return
		if globalSettings.handleWebLinks:
			self.load(url)
		else:
			QDesktopServices.openUrl(url)

	def findText(self, text, flags):
		options = QWebPage.FindFlag.FindWrapsAroundDocument
		if flags & QTextDocument.FindFlag.FindBackward:
			options |= QWebPage.FindFlag.FindBackward
		if flags & QTextDocument.FindFlag.FindCaseSensitively:
			options |= QWebPage.FindFlag.FindCaseSensitively
		return super().findText(text, options)
