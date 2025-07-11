import json
import os
import time
from pathlib import Path

import requests
import tqdm
from dotenv import load_dotenv

from utils import LawDocument

load_dotenv()

OPENLEG_API_KEY = os.getenv("OPENLEG_API_KEY")


class NYLawsClient:
    BASE_URL = "https://legislation.nysenate.gov/api/3"

    def __init__(self, rate_limit_delay=0.5):
        self.session = requests.Session()
        self.rate_limit_delay = rate_limit_delay

    def _make_request(self, endpoint, params=None):
        url = f"{self.BASE_URL}/{endpoint}"
        params["key"] = OPENLEG_API_KEY
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            time.sleep(self.rate_limit_delay)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed for {url}: {e}")
            return None

    def get_all_laws(self):
        data = self._make_request("laws", params={"limit": 1000})
        if not data or not data.get("success"):
            return []

        return [(item["lawId"], item["name"]) for item in data["result"]["items"]]

    def get_law_structure(self, law_id, include_text):
        params = {"full": "true"} if include_text else {}
        data = self._make_request(f"laws/{law_id}", params=params)

        if not data or not data.get("success"):
            return None

        return data["result"]

    def extract_processable_chunks(self, law_id, min_text_length=100):
        law_data = self.get_law_structure(law_id, include_text=True)
        if not law_data:
            return []

        chunks = []
        law_name = law_data["info"]["name"]

        def extract_chunks_recursive(doc, parent_context=""):
            current_context = (
                f"{parent_context} > {doc.get('title', '')}"
                if parent_context
                else doc.get("title", "")
            )

            if doc.get("docType") == "ARTICLE" and doc.get("text"):
                article_text = doc["text"]
                section_texts = []

                if "documents" in doc and "items" in doc["documents"]:
                    section_texts.extend(
                        f"Section {section.get('docLevelId')}: {section['text']}"
                        for section in doc["documents"]["items"]
                        if section.get("text") and len(section["text"]) > min_text_length
                    )

                full_text = article_text
                if section_texts:
                    full_text += "\n\n" + "\n\n".join(section_texts)

                if len(full_text) > min_text_length:
                    chunks.append(
                        LawDocument(
                            law_id=law_id,
                            location_id=doc["locationId"],
                            title=f"{law_name} - {doc.get('title', '')}",
                            doc_type=doc["docType"],
                            text=full_text,
                            active_date=doc.get("activeDate", ""),
                            parent_context=current_context,
                        )
                    )

            elif (
                doc.get("docType") == "SECTION"
                and doc.get("text")
                and len(doc["text"]) > min_text_length * 3
            ):
                chunks.append(
                    LawDocument(
                        law_id=law_id,
                        location_id=doc["locationId"],
                        title=f"{law_name} - Section {doc.get('docLevelId')}",
                        doc_type=doc["docType"],
                        text=doc["text"],
                        active_date=doc.get("activeDate", ""),
                        parent_context=current_context,
                    )
                )

            if "documents" in doc and "items" in doc["documents"]:
                for subdoc in doc["documents"]["items"]:
                    extract_chunks_recursive(subdoc, current_context)

        extract_chunks_recursive(law_data["documents"])

        return chunks


def main():
    client = NYLawsClient()
    laws = client.get_all_laws()
    law_ids = [pair[0] for pair in laws]

    laws = {}

    for law_id in tqdm(law_ids, desc="Processing laws"):
        laws[law_id] = client.get_law_structure(law_id, include_text=True)

    with Path("laws.json").open("w") as fp:
        json.dump(laws, fp)


if __name__ == "__main__":
    main()
