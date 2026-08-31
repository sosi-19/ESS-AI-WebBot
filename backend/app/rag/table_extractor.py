import fitz
import re
from typing import List, Dict, Any, Optional


# ============================================================
# TABLE EXTRACTOR
# ============================================================

class TableExtractor:
    """
    Extract tables from ESS PDF reports using PyMuPDF.

    Designed to plug into the existing ESS AI RAG pipeline.

    Output:
        Each extracted table becomes one RAG chunk containing:
        - normal table representation
        - semantic representation
        - metadata
        - page number
        - table number
        - file_id
    """

    def __init__(self):
        pass

    # ========================================================
    # CLEAN CELL
    # ========================================================

    def clean_cell(self, value: Any) -> str:
        """
        Clean an individual table cell.
        """

        if value is None:
            return ""

        text = str(value)

        # Replace line breaks
        text = text.replace("\n", " ")

        # Replace tabs
        text = text.replace("\t", " ")

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove spaces before %
        text = re.sub(r"\s+%", "%", text)

        # Remove spaces before commas
        text = re.sub(r"\s+,", ",", text)

        # Remove spaces before periods
        text = re.sub(r"\s+\.", ".", text)

        # Remove spaces around slashes
        text = re.sub(r"\s*/\s*", "/", text)

        # Remove spaces around hyphens
        text = re.sub(r"\s+-\s+", "-", text)

        return text.strip()

    # ========================================================
    # CLEAN ROW
    # ========================================================

    def clean_row(
        self,
        row: List[Any]
    ) -> List[str]:

        if row is None:
            return []

        return [
            self.clean_cell(cell)
            for cell in row
        ]

    # ========================================================
    # EMPTY ROW
    # ========================================================

    def is_empty_row(
        self,
        row: List[str]
    ) -> bool:

        if not row:
            return True

        return not any(
            cell.strip()
            for cell in row
        )

    # ========================================================
    # NORMALIZE ROWS
    # ========================================================

    def normalize_rows(
        self,
        rows: List[List[str]]
    ) -> List[List[str]]:

        if not rows:
            return []

        max_columns = max(
            len(row)
            for row in rows
        )

        normalized = []

        for row in rows:

            new_row = list(row)

            while len(new_row) < max_columns:
                new_row.append("")

            normalized.append(new_row)

        return normalized

    # ========================================================
    # FIND TABLES ON PAGE
    # ========================================================

    def extract_page_tables(
        self,
        page,
        page_number: int
    ) -> List[Dict[str, Any]]:

        tables = []

        # ----------------------------------------------------
        # Check whether find_tables exists
        # ----------------------------------------------------

        if not hasattr(page, "find_tables"):

            print(
                f"❌ PyMuPDF table extraction "
                f"is not available on page {page_number}"
            )

            return []

        # ----------------------------------------------------
        # Detect tables
        # ----------------------------------------------------

        try:

            finder = page.find_tables()

        except Exception as e:

            print(
                f"❌ Table detection failed "
                f"on page {page_number}: {e}"
            )

            return []

        # ----------------------------------------------------
        # Get tables
        # ----------------------------------------------------

        try:

            page_tables = finder.tables

        except Exception as e:

            print(
                f"❌ Could not read detected tables "
                f"on page {page_number}: {e}"
            )

            return []

        if not page_tables:
            return []

        # ----------------------------------------------------
        # Process tables
        # ----------------------------------------------------

        for table_index, table in enumerate(
            page_tables,
            start=1
        ):

            try:

                extracted = table.extract()

            except Exception as e:

                print(
                    f"❌ Failed to extract table "
                    f"{table_index} on page "
                    f"{page_number}: {e}"
                )

                continue

            if not extracted:
                continue

            cleaned_rows = []

            # ------------------------------------------------
            # Clean rows
            # ------------------------------------------------

            for row in extracted:

                if row is None:
                    continue

                cleaned_row = self.clean_row(row)

                if self.is_empty_row(cleaned_row):
                    continue

                cleaned_rows.append(
                    cleaned_row
                )

            # ------------------------------------------------
            # Skip empty tables
            # ------------------------------------------------

            if not cleaned_rows:
                continue

            # ------------------------------------------------
            # Normalize columns
            # ------------------------------------------------

            cleaned_rows = self.normalize_rows(
                cleaned_rows
            )

            # ------------------------------------------------
            # Save table
            # ------------------------------------------------

            tables.append({

                "page": page_number,

                "table_index": table_index,

                "rows": cleaned_rows,

                "bbox": getattr(
                    table,
                    "bbox",
                    None
                )

            })

        return tables

    # ========================================================
    # TABLE → NORMAL TEXT
    # ========================================================

    def table_to_text(
        self,
        table: Dict[str, Any]
    ) -> str:

        rows = table.get(
            "rows",
            []
        )

        if not rows:
            return ""

        page = table.get(
            "page"
        )

        table_index = table.get(
            "table_index"
        )

        output = []

        output.append(
            f"TABLE {table_index} FROM PAGE {page}"
        )

        output.append("")

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        header = rows[0]

        output.append(
            " | ".join(header)
        )

        output.append(
            "-" * 80
        )

        # ----------------------------------------------------
        # Data rows
        # ----------------------------------------------------

        for row in rows[1:]:

            output.append(
                " | ".join(row)
            )

        return "\n".join(output)

    # ========================================================
    # TABLE → SEMANTIC TEXT
    # ========================================================

    def table_to_semantic_text(
        self,
        table: Dict[str, Any]
    ) -> str:

        """
        Convert table rows into semantic text.

        Example:

        Indicator | June 2018

        General inflation | 15.1%

        becomes:

        Indicator: General inflation;
        June 2018: 15.1%

        This improves RAG retrieval for questions
        asking about exact table values.
        """

        rows = table.get(
            "rows",
            []
        )

        if not rows:
            return ""

        page = table.get(
            "page"
        )

        table_index = table.get(
            "table_index"
        )

        output = []

        output.append(
            "ESS statistical table."
        )

        output.append(
            f"Page: {page}."
        )

        output.append(
            f"Table number: {table_index}."
        )

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        headers = rows[0]

        # ----------------------------------------------------
        # Convert rows
        # ----------------------------------------------------

        for row in rows[1:]:

            values = []

            for index, cell in enumerate(row):

                if not cell:
                    continue

                if index < len(headers):

                    header = headers[index]

                    if header:

                        values.append(
                            f"{header}: {cell}"
                        )

                    else:

                        values.append(
                            cell
                        )

                else:

                    values.append(
                        cell
                    )

            if values:

                output.append(
                    "; ".join(values)
                )

        return "\n".join(output)

    # ========================================================
    # EXTRACT ALL TABLES FROM PDF
    # ========================================================

    def extract_from_pdf(
        self,
        pdf_path: str
    ) -> List[Dict[str, Any]]:

        print(
            "\n========================================"
        )

        print(
            "📊 TABLE EXTRACTION STARTED"
        )

        print(
            "PDF:",
            pdf_path
        )

        print(
            "========================================"
        )

        all_tables = []

        # ----------------------------------------------------
        # Open PDF
        # ----------------------------------------------------

        try:

            document = fitz.open(
                pdf_path
            )

        except Exception as e:

            print(
                "❌ Could not open PDF:"
            )

            print(e)

            return []

        # ----------------------------------------------------
        # Process PDF
        # ----------------------------------------------------

        try:

            total_pages = len(
                document
            )

            print(
                "Pages:",
                total_pages
            )

            for page_index in range(
                total_pages
            ):

                page_number = page_index + 1

                page = document[
                    page_index
                ]

                print(
                    f"\n📄 Checking page "
                    f"{page_number}/{total_pages}"
                )

                page_tables = (
                    self.extract_page_tables(
                        page,
                        page_number
                    )
                )

                if not page_tables:

                    print(
                        "   No tables found."
                    )

                    continue

                print(
                    f"   ✅ Tables found: "
                    f"{len(page_tables)}"
                )

                for table in page_tables:

                    print(
                        f"   📊 Table "
                        f"{table['table_index']}"
                    )

                    print(
                        f"   Rows: "
                        f"{len(table['rows'])}"
                    )

                    all_tables.append(
                        table
                    )

        finally:

            document.close()

        # ----------------------------------------------------
        # Finished
        # ----------------------------------------------------

        print(
            "\n========================================"
        )

        print(
            "📊 TABLE EXTRACTION COMPLETE"
        )

        print(
            "Total tables:",
            len(all_tables)
        )

        print(
            "========================================\n"
        )

        return all_tables

    # ========================================================
    # CREATE RAG TABLE CHUNKS
    # ========================================================

    def extract_table_chunks(
        self,
        pdf_path: str,
        document_name: str,
        category: str = "PDF",
        file_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:

        """
        Extract PDF tables and convert them
        into chunks compatible with the RAG system.
        """

        tables = self.extract_from_pdf(
            pdf_path
        )

        chunks = []

        # ----------------------------------------------------
        # Convert each table into a chunk
        # ----------------------------------------------------

        for table in tables:

            # ------------------------------------------------
            # Normal table
            # ------------------------------------------------

            table_text = self.table_to_text(
                table
            )

            # ------------------------------------------------
            # Semantic table
            # ------------------------------------------------

            semantic_text = (
                self.table_to_semantic_text(
                    table
                )
            )

            if not table_text:
                continue

            page = table.get(
                "page"
            )

            table_index = table.get(
                "table_index"
            )

            # ------------------------------------------------
            # Final RAG text
            # ------------------------------------------------

            final_text = (
                f"{table_text}\n\n"
                f"TABLE DATA:\n"
                f"{semantic_text}"
            )

            # ------------------------------------------------
            # Metadata
            # ------------------------------------------------

            metadata = {

                "document":
                    document_name,

                "category":
                    category,

                "type":
                    "table",

                "page":
                    page,

                "table_index":
                    table_index,

                "path":
                    pdf_path,

                "file_id":
                    file_id

            }

            # ------------------------------------------------
            # Chunk
            # ------------------------------------------------

            chunk = {

                "text":
                    final_text,

                "document":
                    document_name,

                "category":
                    category,

                "type":
                    "table",

                "page":
                    page,

                "table_index":
                    table_index,

                "path":
                    pdf_path,

                "file_id":
                    file_id,

                "metadata":
                    metadata

            }

            chunks.append(
                chunk
            )

        # ====================================================
        # DEBUG OUTPUT
        # ====================================================

        print(
            "\n========== TABLE RAG CHUNKS =========="
        )

        print(
            "Total table chunks:",
            len(chunks)
        )

        for index, chunk in enumerate(
            chunks,
            start=1
        ):

            print(
                f"\nTABLE CHUNK #{index}"
            )

            print(
                f"Page: {chunk['page']}"
            )

            print(
                f"Table: {chunk['table_index']}"
            )

            print(
                f"Characters: "
                f"{len(chunk['text'])}"
            )

            print(
                chunk["text"][:2000]
            )

        print(
            "\n=======================================\n"
        )

        return chunks


# ============================================================
# SIMPLE FUNCTION
# ============================================================

def extract_tables_from_pdf(
    pdf_path: str,
    document_name: str,
    category: str = "PDF",
    file_id: Optional[str] = None
) -> List[Dict[str, Any]]:

    """
    Convenience function.
    """

    extractor = TableExtractor()

    return extractor.extract_table_chunks(
        pdf_path=pdf_path,
        document_name=document_name,
        category=category,
        file_id=file_id
    )