import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QMessageBox, QLabel, QGroupBox, QGridLayout
)
from PyQt5.QtGui import QColor, QPalette, QFont
from PyQt5.QtCore import Qt
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import Firebase
import pandas as pd

url = r"https://tigernet.princeton.edu/s/1760/02-tigernet/index.aspx?sid=1760&gid=2&pgid=6#/Search/Advanced"
labels_to_search = ["First Name", "Last Name", "Name", "Primary Email", "Primary Phone", "Preferred Year", "Employer"]
extended_list = labels_to_search.copy()
extended_list.append("Prefix")
dictionized = {key: [] for key in extended_list}
autosave_directory = "autosave.csv"
print(dictionized)


class TitleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setFixedHeight(120)

        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        self.setStyleSheet("""
            background-color: #FFB74D; /* Lightest Orange */
            border-radius: 30px;
            color: white;
            font-size: 30px;
        """)

        title_label = QLabel('TigerLaunch Webscraper')
        title_label.setFont(QFont('Arial', 30, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: white;
        """)

        title_layout.addWidget(title_label)
        self.setLayout(title_layout)


class WebScraperUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.driver = None
        self.aggregated_data = []

    def initUI(self):
        # Set the main layout
        main_layout = QVBoxLayout()

        # Apply styles
        self.setStyleSheet("""
                    QWidget {
                        background-color: white;
                        color: black;
                    }
                    QPushButton {
                        background-color: rgb(255, 165, 0);
                        color: white;
                        border: none;
                        padding: 10px;
                        font-size: 16px;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: rgb(255, 69, 0);
                    }
                    QGroupBox {
                        font-size: 18px;
                        font-weight: bold;
                        color: black;
                        border: 1px solid orange;
                        border-radius: 5px;
                        margin-top: 10px;
                    }
                    QLabel {
                        font-size: 16px;
                    }
                """)

        # Title
        title = TitleWidget()
        main_layout.addWidget(title)
        # Setup Group Box
        setup_group = QGroupBox('Setup')
        setup_layout = QGridLayout()

        self.firebase_indicator = QLabel('Disconnected')
        self.webdriver_indicator = QLabel('Not Launched')

        self.set_indicator_color(self.firebase_indicator, QColor('red'))
        self.set_indicator_color(self.webdriver_indicator, QColor('red'))

        self.connect_firebase_button = QPushButton('Connect to Firebase')
        self.launch_webdriver_button = QPushButton('Launch WebDriver')

        self.connect_firebase_button.clicked.connect(self.connect_to_firebase)
        self.launch_webdriver_button.clicked.connect(self.launch_webdriver)

        setup_layout.addWidget(self.connect_firebase_button, 0, 0)
        setup_layout.addWidget(self.firebase_indicator, 0, 1)
        setup_layout.addWidget(self.launch_webdriver_button, 1, 0)
        setup_layout.addWidget(self.webdriver_indicator, 1, 1)

        setup_group.setLayout(setup_layout)

        # Usage Group Box
        usage_group = QGroupBox('Usage')
        usage_layout = QVBoxLayout()

        self.scrape_button = QPushButton('Scrape Web')
        self.save_button = QPushButton('Save to CSV')

        self.scrape_button.clicked.connect(self.scrape_web)
        self.save_button.clicked.connect(self.save_to_csv)

        usage_layout.addWidget(self.scrape_button)
        usage_layout.addWidget(self.save_button)

        usage_group.setLayout(usage_layout)

        # Add groups to main layout
        main_layout.addWidget(setup_group)
        main_layout.addWidget(usage_group)

        # Set the layout to the window
        self.setLayout(main_layout)

        # Set window properties
        self.setWindowTitle('TigerLaunch Webscraper')
        self.setGeometry(300, 300, 600, 500)
        self.show()

    def set_indicator_color(self, label, color):
        palette = label.palette()
        palette.setColor(QPalette.Window, color)
        label.setAutoFillBackground(True)
        label.setPalette(palette)

    def update_firebase_indicator(self, connected):
        if connected:
            self.firebase_indicator.setText('Connected')
            self.set_indicator_color(self.firebase_indicator, QColor('green'))
        else:
            self.firebase_indicator.setText('Disconnected')
            self.set_indicator_color(self.firebase_indicator, QColor('red'))

    def update_webdriver_indicator(self, launched):
        if launched:
            self.webdriver_indicator.setText('Launched')
            self.set_indicator_color(self.webdriver_indicator, QColor('green'))
        else:
            self.webdriver_indicator.setText('Not Launched')
            self.set_indicator_color(self.webdriver_indicator, QColor('red'))

    def scrape_web(self):
        source = self.driver.page_source
        soup = BeautifulSoup(source, features="html.parser")

        # First check if you have logged in.
        login_buttons = soup.find_all("input", {"class": "buttonSsoLogin"})
        if len(login_buttons) > 0:
            QMessageBox.warning(self, 'Login to TigerNet', 'You need to login to TigerNet first!')
            return -1

        containers = soup.find_all("div", {"class": "imod-directory-member-data-container"})
        if len(containers) == 0:
            QMessageBox.warning(self, 'No results found', 'Make sure you are on the correct webpage')
            return -2

        # The people categories and their corresponding string class years
        people = [container.find("div", {"class": "imod-directory-member-name"}) for container in containers]
        class_years = [container.find("div", {"class": "imod-directory-member-classyear"}).decode_contents() for
                       container in containers]

        print("People: " + str(people))
        print("Class Years: " + str(class_years))

        for person in people:
            print(person)
            link = person.find("a")
            link_url = link["href"]

            name = link.decode_contents()

            if Firebase.connected and Firebase.user_exists("alumni", name):
                continue

            self.driver.get(link_url)
            time.sleep(2)

            person_info = self.scrape_link()
            if not person_info:
                pass
            else:
                for key, value in person_info.items():
                    dictionized[key].append(value)
                df = pd.DataFrame(dictionized)
                df.to_csv(autosave_directory, index=False)

                if Firebase.connected:
                    Firebase.add_data(name, person_info)

            self.driver.back()

    def scrape_link(self):
        source = self.driver.page_source
        soup = BeautifulSoup(source)
        labels = soup.find_all("div", {"class": "imod-profile-field-label ng-binding ng-scope"})
        data = soup.find_all("div", {"class": "imod-profile-field-data ng-binding ng-scope"})

        mapping = {}

        for target in labels_to_search:
            mapping[target] = ""

        for i, label in enumerate(labels):

            for target in labels_to_search:
                if str(label.encode_contents(), "UTF-8") == (target + ":"):
                    mapping[target] = str(data[i].encode_contents(), "UTF-8")

        mapping["Prefix"] = mapping["Name"].partition(' ')[0]  # Extract Prefix
        if mapping["Prefix"] == mapping["First Name"]:
            mapping["Prefix"] = ""

        return mapping

    def save_to_csv(self):
        df = pd.DataFrame(dictionized)
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dir_name = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv);;All Files (*)")[0]
        if dir_name:
            df.to_csv(dir_name, index=False)
            QMessageBox.information(self, 'Info', 'Saved to ' + dir_name)
        else:
            QMessageBox.warning(self, 'Save failed', 'CSV was not saved to a directory')

    def connect_to_firebase(self):
        connected, msg = Firebase.initialize_firebase()
        if not connected:
            QMessageBox.warning(self, 'Failed to Connect', msg)
            self.update_firebase_indicator(False)
        else:
            self.update_firebase_indicator(True)

    def launch_webdriver(self):
        try:
            options = webdriver.ChromeOptions()
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            self.driver.get(url)
            self.update_webdriver_indicator(True)
        except:
            self.update_webdriver_indicator(False)
            QMessageBox.warning(self, 'WebDriver Failure', 'Failed to launch WebDriver')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = WebScraperUI()
    sys.exit(app.exec_())