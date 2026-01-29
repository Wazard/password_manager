import gzip

def compress_data(data_str: str) -> bytes:
    return gzip.compress(data_str.encode('utf-8'))

def decompress_data(compressed_data: bytes) -> str:
    return gzip.decompress(compressed_data).decode('utf-8')