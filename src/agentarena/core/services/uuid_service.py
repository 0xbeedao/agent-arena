from typing import List

from sqlmodel import Field
from ulid import ULID


class UUIDService:
    """
    Creates IDs for everything.
    """

    def __init__(
        self,
        word_list: List[str] = Field(description="The word list to use"),
        prod: bool = False,
    ):
        self.word_list = word_list
        self.prod = prod

    def make_id(self):
        base = ULID()
        if self.prod or not self.word_list:
            return base.hex

        val = int.from_bytes(base.bytes[-8:])
        return encode_arbitrary_base(val, self.word_list)

    def ensure_id(self, obj):
        id = getattr(obj, "id", "")
        if id is None or id == 0 or id == "":
            return self.make_id()
        return id


def get_wordlist(
    filename: str,
):
    with open(filename, "r") as file:
        lines = file.readlines()
        words = [word.replace("\n", "").lower() for word in lines]
        caps = [word.upper() for word in words]
        words.extend(caps)
        proper = [word.capitalize() for word in words]
        words.extend(proper)
        # revcap = [f"{word[:-1].lower()}{word[-1].upper()}" for word in words]
        # words.extend(revcap)
        return words


def encode_arbitrary_base(number, words):
    """Encodes an integer using the specified list of words as the arbitrary base."""
    if number < 0:
        raise ValueError("Number must be non-negative")

    base = len(words)
    result = []

    while number > 0:
        remainder = number % base
        result.append(words[remainder])
        number = number // base

    result.reverse()
    return "-".join(result) if result else words[0]


def decode_arbitrary_base(encoded_string, words):
    """Decodes a string encoded by the encode_arbitrary_base function back to an integer."""
    base = len(words)
    number = 0

    if encoded_string == words[0]:
        return 0

    parts = encoded_string.split("-")
    for i, part in enumerate(parts):
        digit = words.index(part)
        number += digit * (base ** (len(parts) - i - 1))

    return number


# # Example usage:
# words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
# number = 10

# encoded = encode_arbitrary_base(number, words)
# print(f"Encoded {number} as: {encoded}")

# decoded = decode_arbitrary_base(encoded, words)
# print(f"Decoded {encoded} as: {decoded}")

# # Base-16 example:
# hex_words = [str(i) for i in range(16)]
# hex_number = 16**2 + 16**1 + 16**0  # 273 in decimal, should be "111" in hex
# hex_encoded = encode_arbitrary_base(hex_number, hex_words)
# print(f"Base-16 encoded {hex_number} as: {hex_encoded}")
# hex_decoded = decode_arbitrary_base(hex_encoded, hex_words)
# print(f"Base-16 decoded {hex_encoded} as: {hex_decoded}")
