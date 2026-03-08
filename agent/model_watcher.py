import hashlib
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ModelHandler(FileSystemEventHandler):
    def __init__(self, models_dir):
        self.models_dir = models_dir
        self.models = {}

    def on_modified(self, event):
        if event.is_directory:
            return
        model_hash = self.hash_model(event.src_path)
        self.models[event.src_path] = model_hash

    def hash_model(self, model_path):
        hasher = hashlib.sha256()
        with open(model_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

def watch_models(models_dir='/workspace/models'):
    event_handler = ModelHandler(models_dir)
    observer = Observer()
    observer.schedule(event_handler, models_dir, recursive=True)
    observer.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    return event_handler.models