from dataclasses import dataclass


@dataclass
class LawDocument:
    law_id: str
    location_id: str
    title: str
    doc_type: str
    text: str
    active_date: str
    parent_context: str = ""
