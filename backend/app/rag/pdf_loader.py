from pathlib import Path
from pypdf import PdfReader


class PDFLoader:

    def __init__(self, pdf_directory: str):
        self.pdf_directory = Path(pdf_directory)


    def load_documents(self):

        documents = []


        for pdf_file in self.pdf_directory.rglob("*.pdf"):

            try:

                reader = PdfReader(pdf_file)


                for page_number, page in enumerate(
                    reader.pages,
                    start=1
                ):

                    page_text = page.extract_text()


                    if page_text:

                        documents.append({

                            "file_name": pdf_file.name,

                            "category": pdf_file.parent.name,

                            "path": str(pdf_file),

                            "page": page_number,

                            "text": page_text

                        })


                print(
                    f"Loaded: {pdf_file.name} ({len(reader.pages)} pages)"
                )


            except Exception as e:

                print(
                    f"Failed to load {pdf_file.name}: {e}"
                )


        return documents