from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QWidget, QHBoxLayout, QLabel, QPushButton
import webbrowser
import os

class FavoritesManager:
    def __init__(self):
        self.favorites = []

    def load_favorites(self):
        # Implementação para carregar favoritos
        pass

    def save_favorites(self, favorites):
        # Implementação para salvar favoritos
        pass

    def add_favorite(self, fav_list, repo_url):
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        
        repo_link = QLabel(f'<a href="{repo_url}">{repo_url}</a>')
        repo_link.setOpenExternalLinks(True)
        item_layout.addWidget(repo_link)

        open_folder_button = QPushButton("Open Folder")
        open_folder_button.clicked.connect(lambda: self.open_folder(repo_url))
        item_layout.addWidget(open_folder_button)

        item = QListWidgetItem()
        item.setSizeHint(item_widget.sizeHint())
        fav_list.addItem(item)
        fav_list.setItemWidget(item, item_widget)

    def open_folder(self, repo_url):
        # Substitua pelo caminho real onde o repositório está clonado
        repo_path = "/caminho/para/o/repositorio/clonado"
        if os.path.exists(repo_path):
            os.startfile(repo_path)
        else:
            print(f"O caminho {repo_path} não existe.")

    def open_repo(self, repo_url):
        webbrowser.open(repo_url)
