def get_line_at_index(text: str, index: int, separator: str="\n") -> str:
    """
    Returns the entire line containing a specific character index in a multi-line string.

    Args:
        text_string (str): The multi-line string.
        index (int): The character index within the string.

    Returns:
        str: The line containing the specified index, or None if the index is out of bounds.
    """
    lines = text.split(separator)
    currentPos = 0
    for line in lines:
        if currentPos + len(line) + len(separator) > index:
            return line
        currentPos += len(line) + len(separator)


if __name__ == "__main__":
    assert get_line_at_index("something ; another thing", 0, " ; ") == "something"
    assert get_line_at_index("something ; another thing", 8, " ; ") == "something"
    assert get_line_at_index("something ; another thing", 12, " ; ") == "another thing"
    assert get_line_at_index("something ; another thing", 20, " ; ") == "another thing"
    print("Tests passed")