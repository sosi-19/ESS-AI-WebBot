from pathlib import Path

from app.rag.table_extractor import TableExtractor


# ============================================================
# PDF
# ============================================================

PDF_PATH = Path(
    "uploads",
    "temp",
    "9f593073-df1e-4a0f-b7f0-51f5407388ca_"
    "1.inflation-report-june-efy-2018-final.pdf"
)


# ============================================================
# INFORMATION
# ============================================================

DOCUMENT_NAME = (
    "1.inflation-report-june-efy-2018-final.pdf"
)

FILE_ID = (
    "9f593073-df1e-4a0f-b7f0-51f5407388ca"
)


# ============================================================
# START
# ============================================================

print()
print("=" * 60)
print("ESS AI TABLE EXTRACTOR TEST")
print("=" * 60)

print(
    "Current directory:",
    Path.cwd()
)

print(
    "PDF:",
    PDF_PATH
)

print(
    "Resolved PDF:",
    PDF_PATH.resolve()
)

print(
    "Exists:",
    PDF_PATH.exists()
)


# ============================================================
# CHECK PDF
# ============================================================

if not PDF_PATH.exists():

    print()
    print("❌ PDF NOT FOUND")
    print()

    print(
        "Expected:"
    )

    print(
        PDF_PATH.resolve()
    )

    print()

    raise SystemExit(1)


# ============================================================
# CREATE EXTRACTOR
# ============================================================

print()
print("=" * 60)
print("CREATING TABLE EXTRACTOR")
print("=" * 60)

extractor = TableExtractor()


# ============================================================
# EXTRACT
# ============================================================

print()
print("=" * 60)
print("EXTRACTING TABLES")
print("=" * 60)

try:

    chunks = extractor.extract_table_chunks(

        pdf_path=str(
            PDF_PATH
        ),

        document_name=DOCUMENT_NAME,

        category="PDF",

        file_id=FILE_ID

    )

except Exception as e:

    print()
    print("=" * 60)
    print("❌ EXTRACTION ERROR")
    print("=" * 60)

    print(
        "Error type:",
        type(e).__name__
    )

    print(
        "Error:",
        str(e)
    )

    raise


# ============================================================
# RESULTS
# ============================================================

print()
print("=" * 60)
print("FINAL RESULT")
print("=" * 60)

print(
    "Total table chunks:",
    len(chunks)
)


# ============================================================
# PRINT TABLES
# ============================================================

for i, chunk in enumerate(
    chunks,
    start=1
):

    print()
    print("-" * 60)

    print(
        f"TABLE CHUNK #{i}"
    )

    print("-" * 60)

    print(
        "Type:",
        chunk.get("type")
    )

    print(
        "Page:",
        chunk.get("page")
    )

    print(
        "Table:",
        chunk.get("table_index")
    )

    print(
        "Document:",
        chunk.get("document")
    )

    print(
        "File ID:",
        chunk.get("file_id")
    )

    print()

    print(
        chunk.get(
            "text",
            ""
        )
    )


# ============================================================
# FINISHED
# ============================================================

print()
print("=" * 60)
print("✅ TABLE EXTRACTION FINISHED")
print("=" * 60)