import os

def make_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

