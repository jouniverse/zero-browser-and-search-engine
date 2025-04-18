import sys
import os
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QToolBar,
    QLineEdit,
    QPushButton,
    QAction,
    QStatusBar,
    QTabWidget,
    QTabBar,
    QMenu,
    QFileDialog,
)
from PyQt5.QtGui import QIcon, QPixmap

# Make sure QWebEngineProfile is imported
from PyQt5.QtWebEngineWidgets import (
    QWebEngineView,
    QWebEngineProfile,
    QWebEnginePage,
    QWebEngineDownloadItem,
)  # Add QWebEnginePage


class WebEnginePage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.profile = profile
        self._active_downloads = set()

    def createWindow(self, _type):
        main_window = self.view().window()
        if isinstance(main_window, SimpleWebBrowser):
            new_view = QWebEngineView()
            new_page = WebEnginePage(self.profile, new_view)
            new_view.setPage(new_page)
            main_window.add_new_tab_with_view(new_view)
            return new_page
        return None

    def contextMenuEvent(self, event):
        menu = QMenu()
        hit_result = self.contextMenuData()

        # Back, Forward, Reload actions
        back_action = menu.addAction("Back")
        back_action.setEnabled(self.action(QWebEnginePage.Back).isEnabled())
        back_action.triggered.connect(lambda: self.triggerAction(QWebEnginePage.Back))

        forward_action = menu.addAction("Forward")
        forward_action.setEnabled(self.action(QWebEnginePage.Forward).isEnabled())
        forward_action.triggered.connect(
            lambda: self.triggerAction(QWebEnginePage.Forward)
        )

        reload_action = menu.addAction("Reload")
        reload_action.triggered.connect(
            lambda: self.triggerAction(QWebEnginePage.Reload)
        )

        menu.addSeparator()

        # Save page action
        save_page_action = menu.addAction("Save page")
        save_page_action.triggered.connect(
            lambda: self.triggerAction(QWebEnginePage.SavePage)
        )

        # Link specific actions
        if hit_result.linkUrl().isValid():
            new_tab_action = menu.addAction("Open link in new tab")
            new_tab_action.triggered.connect(
                lambda: self.triggerAction(QWebEnginePage.OpenLinkInNewTab)
            )

            menu.addSeparator()

            save_link_action = menu.addAction("Save link as...")
            save_link_action.triggered.connect(
                lambda: self.triggerAction(QWebEnginePage.DownloadLinkToDisk)
            )

            copy_link_action = menu.addAction("Copy link address")
            copy_link_action.triggered.connect(
                lambda: QApplication.clipboard().setText(
                    hit_result.linkUrl().toString()
                )
            )

        # Image specific actions
        if hit_result.mediaType() == QWebEnginePage.MediaTypeImage:
            if not menu.isEmpty():
                menu.addSeparator()

            save_image_action = menu.addAction("Save image as...")
            save_image_action.triggered.connect(
                lambda: self.triggerAction(QWebEnginePage.DownloadImageToDisk)
            )

            copy_image_action = menu.addAction("Copy image")
            copy_image_action.triggered.connect(
                lambda: self.triggerAction(QWebEnginePage.CopyImageToClipboard)
            )

            copy_image_addr_action = menu.addAction("Copy image address")
            copy_image_addr_action.triggered.connect(
                lambda: QApplication.clipboard().setText(
                    hit_result.mediaUrl().toString()
                )
            )

        menu.exec_(event.globalPos())

    def javaScriptConsoleMessage(self, level, message, line, source):
        # Suppress console messages
        pass

    def handle_download(self, download):
        # Clean up completed downloads
        self._active_downloads = {
            d for d in self._active_downloads if not d.isFinished()
        }

        # Cancel any conflicting downloads
        for active_download in self._active_downloads:
            if active_download.state() == QWebEngineDownloadItem.DownloadInProgress:
                active_download.cancel()

        suggested_file = download.suggestedFileName()
        if not suggested_file:
            suggested_file = "download"

        file_path, _ = QFileDialog.getSaveFileName(
            self.view(),
            "Save File",
            os.path.join(os.path.expanduser("~/Downloads"), suggested_file),
        )

        if file_path:
            download.setPath(file_path)

            # Set up download tracking
            def cleanup_download():
                if download in self._active_downloads:
                    self._active_downloads.remove(download)
                download.finished.disconnect(cleanup_download)
                download.downloadProgress.disconnect(update_progress)
                if download.state() == QWebEngineDownloadItem.DownloadCompleted:
                    self.view().window().status_bar.showMessage(
                        f"Download completed: {os.path.basename(file_path)}", 5000
                    )

            def update_progress(bytes_received, bytes_total):
                if (
                    bytes_total > 0
                    and download.state() == QWebEngineDownloadItem.DownloadInProgress
                ):
                    progress = (bytes_received * 100) / bytes_total
                    self.view().window().status_bar.showMessage(
                        f"Downloading: {progress:.1f}%"
                    )

            # Connect signals before accepting
            download.finished.connect(cleanup_download)
            download.downloadProgress.connect(update_progress)

            # Track the download
            self._active_downloads.add(download)

            # Start the download
            download.accept()
        else:
            download.cancel()


class SimpleWebBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- Window Properties ---
        self.setWindowTitle("ZERO")
        self.setGeometry(100, 100, 1024, 768)

        # Set window icon - try SVG first, fallback to PNG
        icon_path = os.path.join("icons", "zero-logo.svg")
        if not os.path.exists(icon_path):
            icon_path = os.path.join("icons", "zero-logo.png")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Set the style sheet
        self.setStyleSheet(
            """
            QMainWindow {
                background: #2b2b2b;
            }
            QToolBar {
                background: #333333;
                border: none;
                padding: 5px;
                spacing: 5px;
            }
            QToolBar QLineEdit {
                background: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
                selection-background-color: #666666;
                min-width: 400px;
            }
            QToolBar QLineEdit:focus {
                border: 1px solid #666666;
                background: #454545;
            }
            QStatusBar {
                background: #333333;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: none;
                background: #2b2b2b;
            }
            QTabBar::tab {
                background: #333333;
                color: #ffffff;
                border: none;
                padding: 8px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #404040;
            }
            QTabBar::tab:hover {
                background: #454545;
            }
            QTabBar::close-button {
                image: url(icons/close.svg);
                subcontrol-position: right;
                margin: 2px;
            }
            QTabBar::close-button:hover {
                background: #666666;
                border-radius: 2px;
            }
            QPushButton, QToolButton {
                background: #404040;
                border: none;
                padding: 5px 10px;
                color: #ffffff;
                border-radius: 3px;
            }
            QPushButton:hover, QToolButton:hover {
                background: #454545;
            }
            QPushButton:pressed, QToolButton:pressed {
                background: #505050;
            }
            QMenu {
                background: #333333;
                color: #ffffff;
                border: 1px solid #404040;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background: #404040;
            }
            QMenu::separator {
                height: 1px;
                background: #404040;
                margin: 5px 0px;
            }
        """
        )

        # Create a profile for the browser
        self.profile = QWebEngineProfile(self)
        self.profile.setDownloadPath(os.path.expanduser("~/Downloads"))
        self.profile.downloadRequested.connect(self.handle_download_request)

        # --- Navigation Toolbar ---
        self.nav_toolbar = QToolBar("Navigation")
        self.addToolBar(self.nav_toolbar)

        # URL Address Bar
        self.url_bar = QLineEdit()
        self.url_bar.setStatusTip("Enter web address and press Enter")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.nav_toolbar.addWidget(self.url_bar)

        # --- Tab Widget ---
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.setCentralWidget(self.tabs)

        # Create initial tabs
        self.add_new_tab(QUrl("https://zero-browser-home.vercel.app/"), "ZERO Home")
        #  Google
        # self.add_new_tab(QUrl("https://www.google.com"), "Google")
        # Zero Search
        self.add_new_tab(QUrl("http://127.0.0.1:5001"), "ZERO Search")

        # Set focus to the first tab
        self.tabs.setCurrentIndex(0)

        # New Tab Button
        new_tab_button = QAction(QIcon("icons/new-tab.svg"), "New Tab", self)
        new_tab_button.setStatusTip("Open a new tab")
        new_tab_button.triggered.connect(lambda: self.add_new_tab())
        self.nav_toolbar.addAction(new_tab_button)

        # Back Button
        back_button = QAction(QIcon("icons/left-arrow.svg"), "Back", self)
        back_button.setStatusTip("Go to the previous page")
        back_button.triggered.connect(self.navigate_back)
        self.nav_toolbar.addAction(back_button)

        # Forward Button
        forward_button = QAction(QIcon("icons/right-arrow.svg"), "Forward", self)
        forward_button.setStatusTip("Go to the next page")
        forward_button.triggered.connect(self.navigate_forward)
        self.nav_toolbar.addAction(forward_button)

        # Refresh Button
        refresh_button = QAction(QIcon("icons/reload.svg"), "Refresh", self)
        refresh_button.setStatusTip("Reload the current page")
        refresh_button.triggered.connect(self.refresh_page)
        self.nav_toolbar.addAction(refresh_button)

        # Home Button
        home_button = QAction(QIcon("icons/home.svg"), "Home", self)
        home_button.setStatusTip("Go to the home page")
        home_button.triggered.connect(self.navigate_home)
        self.nav_toolbar.addAction(home_button)

        # Stop Button
        stop_button = QAction(QIcon("icons/stop.svg"), "Stop", self)
        stop_button.setStatusTip("Stop loading the current page")
        stop_button.triggered.connect(self.stop_loading)
        self.nav_toolbar.addAction(stop_button)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        # Show loading progress
        self.tabs.currentWidget().loadProgress.connect(self.update_status_bar_progress)
        # Show status tips for actions
        # self.page.statusBarMessage.connect(self.status_bar.showMessage)

    def add_new_tab_with_view(self, web_view):
        """Add a new tab with an existing web view."""
        i = self.tabs.addTab(web_view, "New Tab")
        self.tabs.setCurrentIndex(i)

        # Connect signals
        web_view.urlChanged.connect(
            lambda qurl, browser=web_view: self.update_url_bar(qurl, browser)
        )
        web_view.loadProgress.connect(self.update_status_bar_progress)
        web_view.titleChanged.connect(lambda title, i=i: self.tabs.setTabText(i, title))

        return web_view

    def add_new_tab(self, qurl=None, label="New Tab"):
        """Create a new tab with a new web view."""
        if qurl is None:
            # qurl = QUrl("https://www.google.com")
            # Zero Search
            qurl = QUrl("http://127.0.0.1:5001")

        browser = QWebEngineView()
        page = WebEnginePage(self.profile, browser)
        browser.setPage(page)
        browser.setUrl(qurl)

        return self.add_new_tab_with_view(browser)

    def close_tab(self, i):
        if self.tabs.count() < 2:
            return  # Don't close if it's the last tab

        self.tabs.removeTab(i)

    def current_tab_changed(self, i):
        if i >= 0:
            browser = self.tabs.widget(i)
            self.url_bar.setText(browser.url().toString())
            self.url_bar.setCursorPosition(0)

    def navigate_back(self):
        self.tabs.currentWidget().back()

    def navigate_forward(self):
        self.tabs.currentWidget().forward()

    def refresh_page(self):
        self.tabs.currentWidget().reload()

    def navigate_home(self):
        """Navigates the browser to the predefined home page."""
        # self.tabs.currentWidget().setUrl(QUrl("https://www.google.com"))
        #  Zero Search
        self.tabs.currentWidget().setUrl(QUrl("http://127.0.0.1:5001"))

    def navigate_to_url(self):
        """Navigates to the URL entered in the address bar."""
        url_text = self.url_bar.text().strip()
        if not url_text:
            return  # Do nothing if empty

        # Basic check to add http:// if missing (you might want more robust checks)
        if not url_text.startswith("http://") and not url_text.startswith("https://"):
            url_text = "https://" + url_text  # Default to https

        q = QUrl(url_text)
        # Optional: Add simple validation
        # if q.isValid():
        self.tabs.currentWidget().setUrl(q)
        # else:
        #     self.status_bar.showMessage("Invalid URL entered", 3000)

    def update_url_bar(self, qurl, browser=None):
        """Updates the address bar text when the browser navigates."""
        if browser != self.tabs.currentWidget():
            return

        # Don't update if the user is currently typing
        if not self.url_bar.hasFocus():
            self.url_bar.setText(qurl.toString())
            self.url_bar.setCursorPosition(0)  # Move cursor to start

    def update_status_bar_progress(self, progress):
        """Updates the status bar to show loading progress."""
        if 0 < progress < 100:
            self.status_bar.showMessage(f"Loading... {progress}%")
        elif progress == 100:
            self.status_bar.clearMessage()  # Clear message when done
        # else: progress == 0 (or error), handled by statusBarMessage

    def stop_loading(self):
        self.tabs.currentWidget().stop()

    def handle_download_request(self, download):
        # Forward download to the current page
        current_page = self.tabs.currentWidget().page()
        current_page.handle_download(download)


# --- Main Execution ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Set Application Name and Icon
    app.setApplicationName("ZERO Browser")

    # Set app icon - try SVG first, fallback to PNG
    icon_path = os.path.join("icons", "zero-logo.svg")
    if not os.path.exists(icon_path):
        icon_path = os.path.join("icons", "zero-logo.png")

    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = SimpleWebBrowser()
    window.show()

    sys.exit(app.exec_())  # Start the event loop
