import sys
import os
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QToolBar,
    QLineEdit,
    QAction,
    QProgressBar,
    QStatusBar,
    QTabWidget,
    QFileDialog,
    QWidget,
    QVBoxLayout
)
from PyQt5.QtWebEngineWidgets import QWebEngineView


class MultiTabBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        # Track the user's custom background image file path
        self.custom_bg_path = ""

        # Set window defaults
        self.setWindowTitle('Custom Python Browser with Tabs')
        self.resize(1200, 800)

        # Create Tab Widget container
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.setCentralWidget(self.tabs)

        # Setup UI components
        self.create_navbar()
        self.create_statusbar()

        # Open default starting tab
        self.add_new_tab(QUrl('https://google.com'), 'Homepage')

    def create_navbar(self):
        """Creates the navigation toolbar with multi-tab actions."""
        navbar = QToolBar("Navigation")
        self.addToolBar(navbar)

        # Back Button
        back_btn = QAction('◀', self)
        back_btn.triggered.connect(lambda: self.current_browser().back())
        navbar.addAction(back_btn)

        # Forward Button
        forward_btn = QAction('▶', self)
        forward_btn.triggered.connect(lambda: self.current_browser().forward())
        navbar.addAction(forward_btn)

        # Refresh Button
        reload_btn = QAction('⟳', self)
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        navbar.addAction(reload_btn)

        # Home Button
        home_btn = QAction('🏠', self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)

        # New Tab Button (+)
        new_tab_btn = QAction('➕', self)
        new_tab_btn.setStatusTip('Open a new tab')
        new_tab_btn.triggered.connect(lambda: self.add_new_tab(QUrl('https://google.com'), 'New Tab'))
        navbar.addAction(new_tab_btn)

        navbar.addSeparator()

        # URL Input Bar
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        navbar.addSeparator()

        # Custom Background Button
        bg_btn = QAction('🖼️ Set Google BG', self)
        bg_btn.setStatusTip('Select a custom local image for Google background')
        bg_btn.triggered.connect(self.choose_background_image)
        navbar.addAction(bg_btn)

    def create_statusbar(self):
        """Creates a status bar at the bottom containing a progress bar."""
        self.setStatusBar(QStatusBar(self))
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(15)
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setTextVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)

    def current_browser(self):
        """Helper to get the active QWebEngineView tab."""
        return self.tabs.currentWidget()

    def add_new_tab(self, qurl, label):
        """Creates a new browser instance inside a fresh tab."""
        browser = QWebEngineView()
        browser.setUrl(qurl)

        # Add to tabs and select it
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

        # Connect specific tab events to main window handlers
        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_url_bar(qurl, browser))
        browser.loadProgress.connect(lambda progress, browser=browser: self.update_progress(progress, browser))
        browser.loadFinished.connect(lambda success, browser=browser: self.handle_load_finished(success, browser))

    def tab_open_doubleclick(self, i):
        """Opens a new tab if empty space is double-clicked."""
        if i == -1:
            self.add_new_tab(QUrl('https://google.com'), 'New Tab')

    def close_current_tab(self, i):
        """Closes target tab index while safeguarding last remaining tab."""
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(i)

    def current_tab_changed(self, i):
        """Syncs URL text and page titles when alternating between tabs."""
        qurl = self.current_browser().url()
        self.url_bar.setText(qurl.toString())
        self.setWindowTitle(f"{self.current_browser().page().title()} - Custom Python Browser")

    def navigate_home(self):
        self.current_browser().setUrl(QUrl('https://google.com'))

    def navigate_to_url(self):
        text_input = self.url_bar.text().strip()
        if not text_input.startswith(('http://', 'https://')):
            if '.' in text_input and ' ' not in text_input:
                url_string = 'https://' + text_input
            else:
                url_string = f'https://google.com{text_input.replace(" ", "+")}'
        else:
            url_string = text_input
        self.current_browser().setUrl(QUrl(url_string))

    def update_url_bar(self, qurl, browser):
        """Updates URL bar text if the event source is the currently visible tab."""
        if browser == self.current_browser():
            self.url_bar.setText(qurl.toString())

    def update_progress(self, progress, browser):
        """Updates progress tracking bar if the source is the currently visible tab."""
        if browser == self.current_browser():
            self.progress_bar.setValue(progress)

    def choose_background_image(self):
        """Prompts user to select a picture file and refreshes current view to apply it."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if file_path:
            # Convert file path to use absolute forward-slashes for valid CSS rendering strings
            self.custom_bg_path = file_path.replace('\\', '/')
            self.current_browser().reload()

    def handle_load_finished(self, success, browser):
        """Injects custom CSS styling code on Google if a background file is selected."""
        if browser == self.current_browser():
            self.progress_bar.setValue(0)
            self.setWindowTitle(f"{browser.page().title()} - Custom Python Browser")
            if not success:
                self.statusBar().showMessage("Failed to load page.", 3000)

        # Target Google instances to inject custom CSS
        current_url = browser.url().toString()
        if "google.com" in current_url and self.custom_bg_path:
            # Build JavaScript snippet to inject layout styling changes
            css_injection = f"""
            (function() {{
                var style = document.createElement('style');
                style.type = 'text/css';
                style.innerHTML = `
                    body, #gsr, #viewport, .goxp {{
                        background-image: url('file:///{self.custom_bg_path}') !important;
                        background-size: cover !important;
                        background-position: center center !important;
                        background-repeat: no-repeat !important;
                        background-attachment: fixed !important;
                    }}
                    /* Make text containers transparent so the background passes through cleanly */
                    #searchform, .sfbg, .logo, #footcnt, .fbar, #cnt {{
                        background: transparent !important;
                    }}
                `;
                document.getElementsByTagName('head')[0].appendChild(style);
            }})();
            """
            browser.page().runJavaScript(css_injection)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MultiTabBrowser()
    window.show()
    sys.exit(app.exec_())
