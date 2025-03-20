from typing import TextIO


def metadata_line_iterator(soft_file: TextIO):
    """
    Iterator that iterates through the metadata lines of a SOFT file.
    """
    for line in soft_file:
        if line.startswith("^PLATFORM"):
            break
        if not line.startswith("!Series"):
            continue
        yield line
