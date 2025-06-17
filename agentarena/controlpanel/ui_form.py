from typing import Dict
from typing import List
from typing import Optional

from prompt_toolkit import PromptSession


def InputForm(fields: List[str], title: Optional[str] = None) -> Dict[str, str]:
    """
    Prompt the user for each field in fields, returning a dict of responses.
    Optionally display a title before prompting.
    """
    session = PromptSession()
    responses = {}
    if title is not None:
        print("\n" + str(title) + "\n" + ("-" * len(str(title))))
    for field in fields:
        value = session.prompt(f"{field}: ")
        responses[field] = value
    return responses


if __name__ == "__main__":
    fields = ["name", "height", "width"]
    result = InputForm(fields, title="Create Data")
    print("\nResponse:")
    print(result)
