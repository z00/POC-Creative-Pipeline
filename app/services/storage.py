import os
import shutil
from abc import ABC, abstractmethod


# Interface allows easy swapping to AWS S3 or GCP Cloud Storage later
class StorageBackend(ABC):
    @abstractmethod
    def save_file(self, file_path: str, destination_path: str) -> str:
        pass

    @abstractmethod
    def get_file(self, file_path: str) -> str:
        pass


class LocalStorage(StorageBackend):
    def __init__(self, base_dir: str = "storage"):
        self.base_dir = base_dir
        self.input_dir = os.path.join(base_dir, "inputs")
        self.output_dir = os.path.join(base_dir, "outputs")
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def save_file(self, source_path: str, destination_subpath: str) -> str:
        dest = os.path.join(self.output_dir, destination_subpath)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(source_path, dest)
        return dest

    def get_file(self, filename: str) -> str:
        # Check input folder for existing assets
        path = os.path.join(self.input_dir, filename)
        return path if os.path.exists(path) else None
