import re


CSV_KEYWORDS = [
    "average",
    "mean",
    "count",
    "maximum",
    "minimum",
    "max",
    "min",
    "sum",
    "dataset",
    "csv",
    "record",
    "rows",
    "column",
    "unique"
]


PDF_KEYWORDS = [
    "report",
    "survey",
    "publication",
    "document",
    "pdf",
    "chapter"
]


def detect_source(question: str):
    q = question.lower()

    # CSV
    for word in CSV_KEYWORDS:
        if re.search(rf"\b{word}\b", q):
            return "csv"

    # PDF
    for word in PDF_KEYWORDS:
        if re.search(rf"\b{word}\b", q):
            return "pdf"

    # default
    return "llm"