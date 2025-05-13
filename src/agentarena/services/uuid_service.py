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
        self.word_list = word_list
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
