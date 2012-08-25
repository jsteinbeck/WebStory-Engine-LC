#!/usr/bin/env python

import sys, os
from PySide.QtCore import QObject, Slot, Property, QUrl, QSize, Qt
from PySide.QtGui import QApplication, QDesktopServices
from PySide.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide.QtWebKit import *



app = QApplication(sys.argv)
wv = QWebView()

wv.setContextMenuPolicy(Qt.NoContextMenu)

page = wv.page()
mainFrame = page.mainFrame()

inspector = QWebInspector()
inspector.setPage(page)

class WebStoryNetworkAccessManager(QNetworkAccessManager):
	def __init__(self, parent=None):
		super(WebStoryNetworkAccessManager, self).__init__(parent)
		self.allowedUrls = set()
		self.allowedHosts = set()
	
	def addAllowedUrl(self, url):
		self.allowedUrls.add(url)
	
	def addAllowedHost(self, host):
		self.allowedHosts.add(host)
	
	def createRequest(self, op, req, outgoingData = 0):
		url = req.url().toString()
		host = req.url().host()
		if (req.url().isRelative() or req.url().scheme() == "file" or host in self.allowedHosts or url in self.allowedUrls):
			print "Requesting file: " + url
			return QNetworkAccessManager.createRequest(self, op, req, outgoingData)
		else:
			print "Dropping non-local URI request: " + url
			return QNetworkAccessManager.createRequest(self, QNetworkAccessManager.GetOperation, QNetworkRequest(QUrl()))


nam = WebStoryNetworkAccessManager()
page.setNetworkAccessManager(nam)


class WebStoryNetwork(QObject):
	def __init__(self, parent=None):
		super(WebStoryNetwork, self).__init__(parent)
	
	@Slot(str)
	def allowUrl(self, url):
		nam.addAllowedUrl(url)
	
	@Slot(str)
	def allowHost(self, host):
		nam.addAllowedHost(host)


class WebStoryWindow(QObject):
	def __init__(self, parent=None):
		super(WebStoryWindow, self).__init__(parent)
		self.isFullscreen = False
	
	@Slot()
	def fullscreen(self):
		self.isFullscreen = True
		wv.showFullScreen()
	
	@Slot()
	def normal(self):
		self.isFullscreen = False
		wv.showNormal()
	
	@Slot(int, int)
	def resize(self, width, height):
		wv.resize(width, height)
	
	@Slot()
	def maximize(self):
		self.isFullscreen = False
		wv.showMaximized()
	
	@Slot(result=bool)
	def isMaximized(self):
		return wv.isMaximized()
	
	@Slot(result=bool)
	def isFullscreen(self):
		return self.isFullscreen
	
	def getWidth(self):
		size = wv.size()
		return size.width()
	
	def setWidth(self, width):
		size = wv.size()
		wv.resize(width, size.height())
	
	def getHeight(self):
		size = wv.size()
		return size.height()
	
	def setHeight(self, height):
		size = wv.size()
		wv.resize(size.width(), height)
	
	width = Property(int, getWidth, setWidth)
	height = Property(int, getHeight, setHeight)


class WebStoryInspector(QObject):
	def __init__(self, parent=None):
		super(WebStoryInspector, self).__init__(parent)
	
	@Slot()
	def show(self):
		inspector.show()
	
	@Slot()
	def hide(self):
		inspector.hide()


class WebStoryHost(QObject):
	def __init__(self, parent=None):
		super(WebStoryHost, self).__init__(parent)
		self.data = {}
		self.win = WebStoryWindow()
		self.net = WebStoryNetwork()
		self.insp = WebStoryInspector()
	
	def getWindow(self):
		return self.win
	
	def getNetwork(self):
		return self.net
	
	def getInspector(self):
		return self.insp
	
	@Slot(str, result=str)
	def get(self, name):
		if name in self.data:
			return self.data[name]
		else:
			return ""
	
	@Slot(str, result=bool)
	def has(self, name):
		return name in self.data
	
	@Slot(str, str)
	def set(self, name, value):
		self.data[name] = value
	
	@Slot()
	def maximizeWindow(self):
		wv.showMaximized()
	
	@Slot(result=bool)
	def windowIsMaximized(self):
		return wv.maximized()
	
	window = Property(WebStoryWindow, getWindow)
	network = Property(WebStoryNetwork, getNetwork)
	inspector = Property(WebStoryInspector, getInspector)


wsehost = WebStoryHost()

QWebSettings.globalSettings().setAttribute(QWebSettings.WebAttribute.DeveloperExtrasEnabled, True)
QWebSettings.globalSettings().setAttribute(QWebSettings.WebAttribute.OfflineStorageDatabaseEnabled, True)
QWebSettings.globalSettings().setAttribute(QWebSettings.WebAttribute.OfflineWebApplicationCacheEnabled, True)
QWebSettings.globalSettings().setAttribute(QWebSettings.WebAttribute.LocalStorageEnabled, True)
QWebSettings.globalSettings().setAttribute(QWebSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)

# Read game file
f = open("wse/game.xml")
xml = f.read()
f.close();

wsehost.set("game.xml", xml)


def add_js():
	mainFrame.addToJavaScriptWindowObject("HOST", wsehost)
	mainFrame.evaluateJavaScript("if (!location.href.match(/^file:\/\//)) { HOST = undefined; }")

@Slot(QUrl)
def open_external_urls(url):
	QDesktopServices.openUrl(url)

page.setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
wv.linkClicked.connect(open_external_urls)

mainFrame.javaScriptWindowObjectCleared.connect(add_js)

wv.load(QUrl("wse/index.html"))


wv.show()
#inspector.show()

app.exec_()
