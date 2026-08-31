from app.services.file_parser import file_parser
from app.rag.chunker import TextChunker
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore


class UploadService:

    def __init__(self):

        self.chunker = TextChunker()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

        # Temporary in-memory storage
        self.uploads = {}


    def process_upload(
        self,
        file_id: str,
        file_name: str,
        file_path: str
    ):

        print("\n" + "=" * 70)
        print("📤 PROCESSING UPLOADED FILE")
        print("=" * 70)

        print("File ID:", file_id)
        print("File name:", file_name)
        print("File path:", file_path)


        # ==================================================
        # 1. Extract PDF text
        # ==================================================

        pages = file_parser.extract_pdf_text(
            file_path
        )

        print(
            "📄 Pages extracted:",
            len(pages)
        )


        # ==================================================
        # 2. Prepare documents
        # ==================================================

        documents = []

        for page in pages:

            documents.append({

                "file_id": file_id,

                "file_name": file_name,

                "document": file_name,

                "category": "UPLOAD",

                "path": file_path,

                "page": page["page"],

                "text": page["text"]

            })


        # ==================================================
        # 3. Create chunks
        # ==================================================

        chunks = self.chunker.chunk_documents(
            documents
        )

        print(
            "🧩 Chunks created:",
            len(chunks)
        )


        # ==================================================
        # 4. Attach file_id to EVERY chunk
        # ==================================================

        for chunk in chunks:

            chunk["file_id"] = file_id

            # Make sure the document name is available
            # to the retriever/vector store.

            if "document" not in chunk:

                chunk["document"] = file_name

            if "file_name" not in chunk:

                chunk["file_name"] = file_name

            if "category" not in chunk:

                chunk["category"] = "UPLOAD"

            if "path" not in chunk:

                chunk["path"] = file_path


        print(
            "🔗 file_id attached to chunks:",
            file_id
        )


        # ==================================================
        # 5. Get chunk texts
        # ==================================================

        texts = [

            chunk["text"]

            for chunk in chunks

        ]


        # ==================================================
        # 6. Create embeddings
        # ==================================================

        embedding_start = __import__(
            "time"
        ).time()

        embeddings = (
            self.embedding_service.embed_texts(
                texts
            )
        )

        print(
            "🧠 Embedding time:",
            round(
                __import__("time").time()
                - embedding_start,
                2
            ),
            "seconds"
        )


        # ==================================================
        # 7. Save into Chroma
        # ==================================================

        self.vector_store.add_chunks(
            chunks,
            embeddings
        )

        print(
            "💾 Uploaded chunks saved to vector store"
        )


        # ==================================================
        # 8. Temporary storage
        # ==================================================

        self.uploads[file_id] = {

            "file_name": file_name,

            "file_path": file_path,

            "chunks": chunks,

            "embeddings": embeddings

        }


        # ==================================================
        # 9. Verify metadata
        # ==================================================

        print(
            "\n========== UPLOAD METADATA CHECK =========="
        )

        if chunks:

            print(
                "First chunk metadata:"
            )

            print({

                "file_id": chunks[0].get(
                    "file_id"
                ),

                "document": chunks[0].get(
                    "document"
                ),

                "file_name": chunks[0].get(
                    "file_name"
                ),

                "category": chunks[0].get(
                    "category"
                ),

                "page": chunks[0].get(
                    "page"
                ),

                "path": chunks[0].get(
                    "path"
                )

            })

        print(
            "===========================================\n"
        )


        # ==================================================
        # 10. Return upload information
        # ==================================================

        return {

            "file_id": file_id,

            "file_name": file_name,

            "chunks": len(chunks),

            "status": (
                "uploaded and indexed successfully"
            )

        }


upload_service = UploadService()