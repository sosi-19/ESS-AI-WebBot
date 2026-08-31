import fitz  # PyMuPDF


class FileParser:

    def extract_pdf_text(self, file_path: str):

        document = fitz.open(file_path)

        pages = []

        for page_number, page in enumerate(document, start=1):

            text = page.get_text()

            pages.append({
                "page": page_number,
                "text": text
            })

        document.close()

        return pages


file_parser = FileParser()