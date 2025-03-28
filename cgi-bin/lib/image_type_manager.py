import io

def is_jpg(file_path):
    with open(file_path, 'rb') as byte:
        return byte.read(2) == b'\xff\xd8'
