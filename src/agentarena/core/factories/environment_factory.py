from pathlib import Path


def get_project_root():
    root = Path(__file__).parent.parent.parent.parent
    print(f"root: {root}")
    return root
