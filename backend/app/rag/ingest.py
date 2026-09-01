from pathlib import Path

from app.rag.pdf_loader import PDFLoader
from app.rag.chunker import TextChunker
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.table_extractor import TableExtractor


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

PDF_DIR = BASE_DIR / "data" / "pdf"

# ============================================================
# LOAD PDFs
# ============================================================

print("\n==============================================")
print("STEP 1: LOADING PDFs")
print("==============================================")

loader = PDFLoader(
    str(PDF_DIR)
)

documents = loader.load_documents()

print(
    f"Loaded {len(documents)} PDF pages"
)


# ============================================================
# NORMAL TEXT CHUNKS
# ============================================================

print("\n==============================================")
print("STEP 2: CREATING TEXT CHUNKS")
print("==============================================")

chunker = TextChunker()

text_chunks = chunker.chunk_documents(
    documents
)

print(
    f"Generated {len(text_chunks)} text chunks"
)


# ============================================================
# TABLE EXTRACTION
# ============================================================

print("\n==============================================")
print("STEP 3: EXTRACTING TABLES")
print("==============================================")

table_extractor = TableExtractor()

table_chunks = []


# Each document from PDFLoader represents one page.
# We only need to extract the PDF once.

processed_pdfs = set()


for document in documents:

    pdf_path = document.get(
        "path"
    )

    if not pdf_path:

        continue

    if pdf_path in processed_pdfs:

        continue

    processed_pdfs.add(
        pdf_path
    )

    document_name = document.get(
        "file_name",
        Path(pdf_path).name
    )

    print(
        f"\n📊 Extracting tables from:"
        f" {document_name}"
    )

    try:

        extracted = (
            table_extractor.extract_table_chunks(

                pdf_path=pdf_path,

                document_name=document_name,

                category=document.get(
                    "category",
                    "PDF"
                ),

                file_id=None

            )
        )

        table_chunks.extend(
            extracted
        )

        print(
            f"✅ Extracted "
            f"{len(extracted)} tables"
        )

    except Exception as e:

        print(
            f"❌ Table extraction failed:"
        )

        print(
            type(e).__name__,
            str(e)
        )


# ============================================================
# COMBINE CHUNKS
# ============================================================

print("\n==============================================")
print("STEP 4: COMBINING CHUNKS")
print("==============================================")

all_chunks = []

all_chunks.extend(
    text_chunks
)

all_chunks.extend(
    table_chunks
)

print(
    f"Text chunks: {len(text_chunks)}"
)

print(
    f"Table chunks: {len(table_chunks)}"
)

print(
    f"Total chunks: {len(all_chunks)}"
)


# ============================================================
# EMBEDDINGS
# ============================================================

print("\n==============================================")
print("STEP 5: GENERATING EMBEDDINGS")
print("==============================================")

embedder = EmbeddingService()

texts = [
    chunk["text"]
    for chunk in all_chunks
]

embeddings = embedder.embed_texts(
    texts
)

print(
    f"Generated {len(embeddings)} embeddings"
)


# ============================================================
# CHROMADB
# ============================================================

print("\n==============================================")
print("STEP 6: SAVING TO CHROMADB")
print("==============================================")

store = VectorStore()

store.reset()

store.add_chunks(
    all_chunks,
    embeddings
)

print(
    f"Stored {store.count()} chunks"
)


# ============================================================
# DONE
# ============================================================

print("\n==============================================")
print("✅ RAG INDEXING COMPLETE")
print("==============================================")

print(
    f"PDF pages: {len(documents)}"
)

print(
    f"Text chunks: {len(text_chunks)}"
)

print(
    f"Table chunks: {len(table_chunks)}"
)

print(
    f"Total chunks: {len(all_chunks)}"
)

print(
    f"ChromaDB: {store.count()}"
)

print("==============================================")
