import os
from formats import is_supported

class FileNavigator:
    
    def __init__(self):
        self.files = []
        self.current_index = -1
    
    def clear(self):
        self.files = []
        self.current_index = -1
    
    def load_from_path(self, path: str):
        if not path:
            self.clear()
            return
        
        path = os.path.abspath(path)
        
        if os.path.isdir(path):
            directory = path
            selected = None
        else:
            directory = os.path.dirname(path)
            selected = path
        
        if not os.path.isdir(directory):
            self.clear()
            return
        
        entries = []
        for name in sorted(os.listdir(directory), key=lambda value: value.lower()):
            full_path = os.path.join(directory, name)
            if os.path.isfile(full_path) and is_supported(full_path):
                entries.append(full_path)
        
        self.files = entries
        
        if selected and selected in self.files:
            self.current_index = self.files.index(selected)
        elif self.files:
            self.current_index = 0
        else:
            self.current_index = -1
    
    def current(self) -> str | None:
        if 0 <= self.current_index < len(self.files):
            return self.files[self.current_index]
        return None
    
    def has_previous(self) -> bool:
        return self.current_index > 0
    
    def has_next(self) -> bool:
        return 0 <= self.current_index < len(self.files) - 1
    
    def previous(self) -> str | None:
        if self.has_previous():
            self.current_index -= 1
            return self.current()
        return self.current()
    
    def next(self) -> str | None:
        if self.has_next():
            self.current_index += 1
            return self.current()
        return self.current()
    
    def go_to_index(self, index: int) -> str | None:
        if 0 <= index < len(self.files):
            self.current_index = index
            return self.current()
        return None
    
    def get_file_at(self, index: int) -> str | None:
        if 0 <= index < len(self.files):
            return self.files[index]
        return None
    
    def get_index_of(self, path: str) -> int:
        if path in self.files:
            return self.files.index(path)
        return -1
