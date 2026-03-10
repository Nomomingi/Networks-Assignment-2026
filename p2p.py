from db import Blob 
from socket import *
from os import *

def create_chunks(file_path):
    # This method will break the file into smaller chunks.
    if not path.exists('chunks'):
        mkdir('chunks')
    
    chunk_size = 1024
    with open(file_path, 'rb') as f:
        chunk_num = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            with open(f'chunks/chunk_{chunk_num}', 'wb') as chunk_file:
                chunk_file.write(chunk)
            chunk_num += 1

    chunk_file.close()


