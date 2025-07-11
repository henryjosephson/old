import json
import re
import time
from pathlib import Path

from anthropic import Anthropic
from anthropic.types.beta.message_create_params import (
    MessageCreateParamsNonStreaming,
)
from anthropic.types.beta.messages.batch_create_params import Request
from dotenv import load_dotenv

import constants

load_dotenv()

client = Anthropic()

law_files = [file for file in Path("laws").glob("*")]

def score_words(
    batch_size: int,
    min_word_len: int,
    max_word_len: int,
    words: list[str],
):
    """Submits batch job to claude"""
    batches = [words[i : i + batch_size] for i in range(0, len(words), batch_size)]

    message_batch = client.beta.messages.batches.create(
        requests=[
            Request(
                custom_id=f"{i}",
                params=MessageCreateParamsNonStreaming(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    temperature=0,
                    system=constants.prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": batch,
                                },
                            ],
                        },
                        {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "{",
                                },
                            ],
                        },
                    ],
                ),
            )
            for i,batch in enumerate(batches)
        ],
    )
    return message_batch.id


def remove_comments(text):
    """Regex removes any python comments"""
    pattern = r"(\\|#).*\n"
    return re.sub(pattern, "", text)


def merge_jsons(list_of_jsons: list[dict]) -> dict:
    """Merges list of jsons into one dict"""
    merged_dict = {}
    for d in list_of_jsons:
        merged_dict.update(d)
    return merged_dict


def load_json_batches(batch_id):
    """Loads json batches from claude"""
    return [
        json.loads(
            "{" + remove_comments(result.result.message.content[0].text),
        )
        for result in client.beta.messages.batches.results(batch_id)
    ]


def main():
    """Main"""
    words = load_wordlist(wl_file)

    batch_id = score_words(
        BATCH_SIZE,
        MIN_WORD_LEN,
        MAX_WORD_LEN,
        words,
    )

    while True:
        message_batch = client.beta.messages.batches.retrieve(batch_id)
        if message_batch.processing_status == "ended":
            break

        print(f"Batch {batch_id} is still processing...")
        time.sleep(60)
    print(message_batch)

    words_json = merge_jsons(load_json_batches(batch_id))

    with Path("data/out/wordscoring.json").open("w") as f:
        json.dump(words_json, f, indent=4)


if __name__ == "__main__":
    main()