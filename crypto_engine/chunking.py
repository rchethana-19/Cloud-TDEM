"""
TDEM Week 3
Secure File Chunking

Splits a file into fixed-size chunks.
"""

# 1 MB chunk size
CHUNK_SIZE = 1024 * 1024


def split_file(file_path, chunk_size=CHUNK_SIZE):
    """
    Split a file into fixed-size binary chunks.

    Returns:
        list of bytes
    """

    chunks = []

    with open(file_path, "rb") as file:

        while True:

            chunk = file.read(chunk_size)

            if not chunk:
                break

            chunks.append(chunk)

    return chunks


def get_chunk_metadata(chunks):
    """
    Generate metadata for each chunk.
    """

    metadata = []

    for index, chunk in enumerate(chunks):

        metadata.append({
            "chunk_index": index,
            "chunk_size": len(chunk)
        })

    return metadata