import sys
import subprocess
import os
import git
import time
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton, QTabWidget, QFileDialog, QMessageBox, QStatusBar
from PyQt5.QtCore import QThread, pyqtSignal

# Constants
FAVORITOS_FILE = 'repos_favoritos.json'
CLONED_REPOS_FILE = 'repos_clonados.json'
UPDATE_INTERVAL = 60  # In seconds

class GitManager:
    @staticmethod
    def get_branches(repo_url):
        try:
            process = subprocess.Popen(["git", "ls-remote", repo_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, err = process.communicate()
            if process.returncode != 0:
                raise Exception(f"Error listing branches: {err.decode()}")
            branches = [line.split()[1].strip() for line in output.decode().splitlines()]
            return [branch.replace("refs/heads/", "").replace("refs/tags/", "") for branch in branches if "refs/heads/" in branch or "refs/tags/" in branch]
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error listing branches: {e}")
            return []

    @staticmethod
    def clone_repo(repo_url, branch, dest_folder):
        try:
            dest_subfolder = os.path.join(dest_folder, branch)
            os.makedirs(dest_subfolder, exist_ok=True)
            QMessageBox.information(None, "Cloning", "Cloning repository...")
            git.Repo.clone_from(repo_url, dest_subfolder, branch=branch)
            QMessageBox.information(None, "Success", "Repository cloned successfully!")
            return dest_subfolder  # Return the path where the repo was cloned
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error cloning repository: {e}")
            return None

    @staticmethod
    def check_updates(repo_url):
        try:
            process = subprocess.Popen(["git", "ls-remote", repo_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, err = process.communicate()
            if process.returncode != 0:
                raise Exception(f"Error checking for updates: {err.decode()}")
            return True  # Placeholder for actual update check
        except Exception:
            return False

class FavoritesManager:
    @staticmethod
    def load_favorites():
        if os.path.exists(FAVORITOS_FILE):
            with open(FAVORITOS_FILE, 'r') as file:
                return json.load(file)
        return []

    @staticmethod
    def save_favorites(favorites):
        with open(FAVORITOS_FILE, 'w') as file:
            json.dump(favorites, file)

class ClonedReposManager:
    @staticmethod
    def load_cloned_repos():
        if os.path.exists(CLONED_REPOS_FILE):
            with open(CLONED_REPOS_FILE, 'r') as file:
                return json.load(file)
        return {}

    @staticmethod
    def save_cloned_repo(repo_url, path):
        cloned_repos = ClonedReposManager.load_cloned_repos()
        cloned_repos[repo_url] = path
        with open(CLONED_REPOS_FILE, 'w') as file:
            json.dump(cloned_repos, file)

class UpdateCheckerThread(QThread):
    update_signal = pyqtSignal(str, str)

    def __init__(self, favorites):
        super().__init__()
        self.favorites = favorites

    def run(self):
        while True:
            for repo in self.favorites:
                repo_url = repo['url']
                updated = GitManager.check_updates(repo_url)
                status = "Updated" if updated else "Updates Available"
                self.update_signal.emit(repo_url, status)
            time.sleep(UPDATE_INTERVAL)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.favorites = FavoritesManager.load_favorites()
        self.cloned_repos = ClonedReposManager.load_cloned_repos()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Git Repository Manager')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        repository_tab = QWidget()
        favorites_tab = QWidget()

        tab_widget.addTab(repository_tab, "Repository")
        tab_widget.addTab(favorites_tab, "Favorites")

        self.init_repository_tab(repository_tab)
        self.init_favorites_tab(favorites_tab)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.update_checker = UpdateCheckerThread(self.favorites)
        self.update_checker.update_signal.connect(self.update_status)
        self.update_checker.start()

    def init_repository_tab(self, tab):
        layout = QVBoxLayout()
        tab.setLayout(layout)

        self.repo_url_input = QLineEdit()
        layout.addWidget(QLabel('Git Repository URL:'))
        layout.addWidget(self.repo_url_input)

        self.branches_list = QListWidget()
        layout.addWidget(QLabel('Available Branches:'))
        layout.addWidget(self.branches_list)

        button_layout = QHBoxLayout()
        list_branches_btn = QPushButton('List Branches')
        list_branches_btn.clicked.connect(self.list_branches)
        button_layout.addWidget(list_branches_btn)

        refresh_branches_btn = QPushButton('Refresh Branches')
        refresh_branches_btn.clicked.connect(self.list_branches)
        button_layout.addWidget(refresh_branches_btn)

        layout.addLayout(button_layout)

        self.selected_branch_input = QLineEdit()
        self.selected_branch_input.setReadOnly(True)
        layout.addWidget(QLabel('Selected Branch:'))
        layout.addWidget(self.selected_branch_input)

        self.dest_folder_input = QLineEdit()
        layout.addWidget(QLabel('Destination Folder:'))
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(self.dest_folder_input)
        browse_btn = QPushButton('Browse')
        browse_btn.clicked.connect(self.browse_folder)
        dest_layout.addWidget(browse_btn)
        layout.addLayout(dest_layout)

        clone_btn = QPushButton('Clone Repository')
        clone_btn.clicked.connect(self.clone_repository)
        layout.addWidget(clone_btn)

        self.branches_list.itemClicked.connect(self.select_branch)

    def init_favorites_tab(self, tab):
        layout = QVBoxLayout()
        tab.setLayout(layout)

        self.favorites_list = QListWidget()
        layout.addWidget(QLabel('Favorite Repositories'))
        layout.addWidget(self.favorites_list)

        button_layout = QHBoxLayout()
        add_favorite_btn = QPushButton('Add Favorite')
        add_favorite_btn.clicked.connect(self.add_favorite)
        button_layout.addWidget(add_favorite_btn)

        remove_favorite_btn = QPushButton('Remove Favorite')
        remove_favorite_btn.clicked.connect(self.remove_favorite)
        button_layout.addWidget(remove_favorite_btn)

        open_location_btn = QPushButton('Open Location')
        open_location_btn.clicked.connect(self.open_favorite_location)
        button_layout.addWidget(open_location_btn)

        layout.addLayout(button_layout)

        check_updates_btn = QPushButton('Check Updates')
        check_updates_btn.clicked.connect(self.check_updates)
        layout.addWidget(check_updates_btn)

        self.update_favorites_list()

    def list_branches(self):
        repo_url = self.repo_url_input.text()
        if repo_url:
            branches = GitManager.get_branches(repo_url)
            self.branches_list.clear()
            self.branches_list.addItems(branches)
            self.status_bar.showMessage('Branches loaded successfully.')

    def select_branch(self, item):
        self.selected_branch_input.setText(item.text())

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_folder_input.setText(folder)

    def clone_repository(self):
        repo_url = self.repo_url_input.text()
        branch = self.selected_branch_input.text()
        dest_folder = self.dest_folder_input.text()
        if repo_url and branch and dest_folder:
            cloned_path = GitManager.clone_repo(repo_url, branch, dest_folder)
            if cloned_path:
                ClonedReposManager.save_cloned_repo(repo_url, cloned_path)  # Save cloned repo path
                self.add_favorite(repo_url, cloned_path)  # Add to favorites after cloning
        else:
            QMessageBox.warning(self, "Warning", "Please fill in all fields correctly.")

    def add_favorite(self, repo_url, path=None):
        if path is None:
            path = os.path.join(self.dest_folder_input.text(), repo_url.split("/")[-1])  # Default path
        if repo_url:
            self.favorites.append({"url": repo_url, "path": path})
            FavoritesManager.save_favorites(self.favorites)
            self.update_favorites_list()
            self.status_bar.showMessage(f'Repository {repo_url} added to favorites.')
        else:
            QMessageBox.warning(self, "Warning", "Please enter a valid URL.")

    def remove_favorite(self):
        selected_items = self.favorites_list.selectedItems()
        if selected_items:
            selected = selected_items[0].text()
            self.favorites = [f for f in self.favorites if f['url'] != selected]
            FavoritesManager.save_favorites(self.favorites)
            self.update_favorites_list()
            self.status_bar.showMessage(f'Repository {selected} removed from favorites.')

    def update_favorites_list(self):
        self.favorites_list.clear()
        self.favorites_list.addItems([f['url'] for f in self.favorites])

    def open_favorite_location(self):
        selected_items = self.favorites_list.selectedItems()
        if selected_items:
            selected = selected_items[0].text()
            favorite = next((f for f in self.favorites if f['url'] == selected), None)
            if favorite:
                repo_path = favorite['path']
                if os.path.exists(repo_path):
                    os.startfile(repo_path)  # Windows
                else:
                    QMessageBox.warning(self, "Warning", f"The path {repo_path} does not exist.")
        else:
            QMessageBox.warning(self, "Warning", "Please select a favorite repository.")

    def check_updates(self):
        for repo in self.favorites:
            repo_url = repo['url']
            updated = GitManager.check_updates(repo_url)
            status = "Updated" if updated else "Updates Available"
            self.status_bar.showMessage(f'{repo_url}: {status}')

    def update_status(self, repo_url, status):
        self.status_bar.showMessage(f'{repo_url}: {status}')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())