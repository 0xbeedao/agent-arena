"""
wordbase.py

A module to encode and decode integers using a custom word-based numeral system.
Each "digit" in this system is a word from a provided word list.
"""

from typing import List


def encode_number_to_words(
    number: int, word_list: List[str], delimiter: str = "-"
) -> str:
    """
    Encodes a non-negative integer into a word-based representation.

    Args:
        number (int): The integer to encode. Must be non-negative.
        word_list (List[str]): List of unique words representing the "digits".
        delimiter (str): Delimiter to separate encoded words. Default is '-'.

    Returns:
        str: The encoded word string, with words separated by the delimiter.

    Raises:
        ValueError: If number is negative or word_list is empty.
    """
    if number < 0:
        raise ValueError("Number must be non-negative.")
    if not word_list:
        raise ValueError("word_list must contain at least one word.")

    base = len(word_list)
    # Special case for zero
    if number == 0:
        return word_list[0]

    digits = []
    n = number
    while n > 0:
        n, rem = divmod(n, base)
        digits.append(word_list[rem])

    # The digits list has least significant word first, reverse it
    return delimiter.join(reversed(digits))


def decode_words_to_number(
    encoded: str, word_list: List[str], delimiter: str = "-"
) -> int:
    """
    Decodes a word-based representation back into the integer.

    Args:
        encoded (str): The encoded word string, with words separated by the delimiter.
        word_list (List[str]): List of unique words representing the "digits".
        delimiter (str): Delimiter used between encoded words. Default is '-'.

    Returns:
        int: The decoded integer.

    Raises:
        ValueError: If any word in the encoded string is not found in word_list.
    """
    if not word_list:
        raise ValueError("word_list must contain at least one word.")

    words = encoded.split(delimiter)
    base = len(word_list)
    number = 0

    for word in words:
        if word not in word_list:
            raise ValueError(f"Word '{word}' not found in word_list.")
        digit = word_list.index(word)
        number = number * base + digit

    return number


# Example usage
if __name__ == "__main__":
    words = ["apple", "banana", "cherry", "date"]
    num = 42
    encoded = encode_number_to_words(num, words)
    print(f"{num} -> {encoded}")
    decoded = decode_words_to_number(encoded, words)
    print(f"{encoded} -> {decoded}")
