import json
from pathlib import Path
from typing import Callable

from utils import LawDocument

Path("laws").mkdir(exist_ok=True)

with Path("laws.json").open() as f:
    laws = json.load(f)

def recursively_apply_func_to_laws(func: Callable, document: LawDocument):
    if document["repealed"]:
        pass

    if document["documents"]["size"] != 0:
        for sub_document in document["documents"]["items"]:
            recursively_apply_func_to_laws(func, sub_document)
    else:
        func(document["lawId"] + document["locationId"], document["text"])

def save_to_dir(title, text):
    with Path(f"laws/{title}.txt").open("w+") as f:
        f.write(text)
    return

def main():
    for law_id in laws:
        if laws[law_id]["documents"]["documents"]["size"] == 0:
            continue
        for document in laws[law_id]["documents"]["documents"]["items"]:
            recursively_apply_func_to_laws(save_to_dir, document)

if __name__ == "__main__":
    main()
