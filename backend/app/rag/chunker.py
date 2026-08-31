class TextChunker:

    def __init__(
        self,
        chunk_size=1000,
        overlap=200
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_documents(self, documents):

        chunks = []

        chunk_id = 1

        for doc in documents:

            text = doc.get("text", "")

            if not text.strip():
                continue

            start = 0

            while start < len(text):

                end = start + self.chunk_size

                chunk_text = text[start:end]

                chunks.append({

                    "chunk_id": chunk_id,

                    # Works for ESS PDFs and uploaded files
                    "document_name": doc.get(
                        "file_name",
                        "Uploaded Document"
                    ),

                    # Works for ESS PDFs and uploaded files
                    "category": doc.get(
                        "category",
                        "Uploaded File"
                    ),

                    # Works for ESS PDFs and uploaded files
                    "path": doc.get(
                        "path",
                        ""
                    ),

                    # Page number (if available)
                    "page": doc.get(
                        "page",
                        None
                    ),

                    # Store the chunk text
                    "text": chunk_text

                })

                chunk_id += 1

                start += self.chunk_size - self.overlap

        return chunks