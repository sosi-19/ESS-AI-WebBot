from sentence_transformers import SentenceTransformer


class EmbeddingService:

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")


    def encode(self, text: str):
        return self.model.encode(text)


    def embed_text(self, text: str):
        return self.model.encode(text).tolist()


    def embed_texts(self, texts: list[str]):
        return self.model.encode(texts).tolist()