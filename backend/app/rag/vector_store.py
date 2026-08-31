import chromadb
from pathlib import Path


class VectorStore:

    def __init__(self):

        BASE_DIR = Path(__file__).resolve().parents[2]

        db_path = BASE_DIR / "chroma_db"

        self.client = chromadb.PersistentClient(
            path=str(db_path)
        )

        self.collection = self.client.get_or_create_collection(
            name="ess_documents"
        )

    # ==================================================
    # RESET COLLECTION
    # ==================================================

    def reset(self):

        try:

            self.client.delete_collection(
                "ess_documents"
            )

        except Exception:

            pass

        self.collection = self.client.get_or_create_collection(
            name="ess_documents"
        )

    # ==================================================
    # ADD CHUNKS
    # ==================================================

    def add_chunks(
        self,
        chunks,
        embeddings,
        batch_size=1000
    ):

        if not chunks:

            print("⚠️ No chunks to store.")

            return

        if len(chunks) != len(embeddings):

            raise ValueError(
                "Number of chunks and embeddings "
                "must be the same."
            )

        total = len(chunks)

        for i in range(
            0,
            total,
            batch_size
        ):

            batch_chunks = chunks[
                i:i + batch_size
            ]

            batch_embeddings = embeddings[
                i:i + batch_size
            ]

            ids = []

            documents = []

            metadatas = []

            for index, chunk in enumerate(
                batch_chunks
            ):

                # -----------------------------------------
                # FILE ID
                # -----------------------------------------

                file_id = chunk.get(
                    "file_id"
                )

                # -----------------------------------------
                # CATEGORY
                # -----------------------------------------

                category = chunk.get(
                    "category",
                    "PDF"
                )

                # -----------------------------------------
                # CHUNK NUMBER
                # -----------------------------------------

                chunk_number = chunk.get(
                    "chunk_id"
                )

                if chunk_number is None:

                    chunk_number = (
                        i + index
                    )

                # -----------------------------------------
                # SOURCE TYPE
                # -----------------------------------------

                source_type = chunk.get(
                    "source_type",
                    chunk.get(
                        "type",
                        "text"
                    )
                )

                # -----------------------------------------
                # UNIQUE ID
                # -----------------------------------------

                if file_id:

                    chunk_id = (
                        f"{category}_"
                        f"{file_id}_"
                        f"{source_type}_"
                        f"{chunk_number}"
                    )

                else:

                    chunk_id = (
                        f"{category}_"
                        f"{source_type}_"
                        f"{chunk_number}"
                    )

                ids.append(
                    chunk_id
                )

                # -----------------------------------------
                # DOCUMENT TEXT
                # -----------------------------------------

                documents.append(
                    chunk.get(
                        "text",
                        ""
                    )
                )

                # -----------------------------------------
                # DOCUMENT NAME
                # -----------------------------------------

                document_name = chunk.get(
                    "document_name"
                )

                if not document_name:

                    document_name = chunk.get(
                        "document"
                    )

                if not document_name:

                    document_name = chunk.get(
                        "file_name"
                    )

                if not document_name:

                    document_name = "Unknown document"

                # -----------------------------------------
                # METADATA
                # -----------------------------------------

                metadata = {

                    "document": document_name,

                    "category": chunk.get(
                        "category",
                        "PDF"
                    ),

                    "source_type": source_type,

                    "path": chunk.get(
                        "path",
                        ""
                    ),

                    "page": chunk.get(
                        "page",
                        0
                    )

                }

                # -----------------------------------------
                # TABLE INFORMATION
                # -----------------------------------------

                if source_type == "table":

                    metadata["type"] = "table"

                    metadata["table_index"] = int(
                        chunk.get(
                            "table_index",
                            0
                        )
                    )

                else:

                    metadata["type"] = "text"

                # -----------------------------------------
                # FILE ID
                # -----------------------------------------

                if file_id:

                    metadata["file_id"] = file_id

                metadatas.append(
                    metadata
                )

            # ---------------------------------------------
            # STORE BATCH
            # ---------------------------------------------

            self.collection.add(

                ids=ids,

                embeddings=batch_embeddings,

                documents=documents,

                metadatas=metadatas

            )

            print(
                f"Stored "
                f"{min(i + batch_size, total)} "
                f"/ {total}"
            )

    # ==================================================
    # GET TOTAL CHUNK COUNT
    # ==================================================

    def count(self):

        return self.collection.count()

    # ==================================================
    # GET ALL CHUNKS FOR ONE DOCUMENT
    # ==================================================

    def get_document_chunks(
        self,
        document_name
    ):

        results = self.collection.get(

            where={
                "document": document_name
            },

            include=[
                "documents",
                "metadatas"
            ]

        )

        documents = results.get(
            "documents",
            []
        )

        metadatas = results.get(
            "metadatas",
            []
        )

        output = []

        for document, metadata in zip(
            documents,
            metadatas
        ):

            output.append({

                "text": document,

                "document": metadata.get(
                    "document",
                    document_name
                ),

                "category": metadata.get(
                    "category",
                    "PDF"
                ),

                "source_type": metadata.get(
                    "source_type",
                    "text"
                ),

                "type": metadata.get(
                    "type",
                    "text"
                ),

                "page": metadata.get(
                    "page",
                    None
                ),

                "table_index": metadata.get(
                    "table_index",
                    None
                ),

                "path": metadata.get(
                    "path",
                    ""
                ),

                "file_id": metadata.get(
                    "file_id",
                    None
                )

            })

        # ---------------------------------------------
        # SORT BY PAGE
        # ---------------------------------------------

        output.sort(

            key=lambda item: (

                item["page"]

                if item["page"] is not None

                else 999999

            )

        )

        return output