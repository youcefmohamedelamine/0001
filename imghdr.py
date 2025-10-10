import os

def what(file, h=None):
    ext = os.path.splitext(file)[1].lower()
    if ext in ['.jpeg', '.jpg']:
        return 'jpeg'
    elif ext == '.png':
        return 'png'
    elif ext == '.gif':
        return 'gif'
    elif ext == '.bmp':
        return 'bmp'
    elif ext == '.webp':
        return 'webp'
    return None
