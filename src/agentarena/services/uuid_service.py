from typing import List

from pydantic import Field
from ulid import ULID

from agentarena.models.dbbase import DbBase
from agentarena.util.wordbase import encode_number_to_words


class UUIDService:
    """
    Creates IDs for everything.
    """

    def __init__(
        self,
        word_list: List[str] = Field(description="The word list to use"),
        prod: bool = False,
    ):
        words = [word.lower() for word in word_list]
        more = [
            f"{word}s" for word in words if not word.endswith("s") or word.endswith("y")
        ]
        words.extend(more)
        leet = [word.replace("i", "1") for word in words if "i" in word]
        leet.extend([word.replace("o", "0") for word in words if "o" in word])
        words.extend(leet)
        leet.extend(words)
        words = leet
        caps = [word.upper() for word in words]
        proper = [word.capitalize() for word in words]
        words.extend(caps)
        words.extend(proper)
        revcap = [f"{word[:-1].lower()}{word[-1].upper()}" for word in words]
        words.extend(revcap)
        self.word_list = words
        self.prod = prod

    def make_id(self):
        base = ULID()
        if self.prod or not self.word_list:
            return base.hex

        val = int.from_bytes(base.bytes)
        return encode_number_to_words(val, word_list=self.word_list)

    def ensure_id(self, obj: DbBase):
        id = getattr(obj, "id", "")
        if id is None or id == 0 or id == "":
            obj.id = self.make_id()
        return obj
