from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.paragraph_extractor import extract_best_paragraph

import re


# ============================================================
# QUESTION INTENT
# ============================================================

def detect_question_intent(question: str) -> str:

    q = question.lower().strip()

    # --------------------------------------------------------
    # Greetings
    # --------------------------------------------------------

    greeting_patterns = [
        "hi",
        "hello",
        "hey",
        "hey there",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
        "what's up",
        "whats up",
        "sup",
    ]

    if q in greeting_patterns:
        return "greeting"

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary_patterns = [
        "summarize",
        "summarise",
        "summary",
        "overview",
        "main points",
        "key findings",
        "key findings of",
        "main findings",
        "describe the report",
        "give me an overview",
        "give me a summary",
        "summarize the report",
        "summarise the report",
        "summary of the report",
        "overview of the report",
    ]

    if any(
        pattern in q
        for pattern in summary_patterns
    ):
        return "summary"

    # --------------------------------------------------------
    # Definition
    # --------------------------------------------------------

    definition_patterns = [
        "define ",
        "definition of",
        "meaning of",
        "what does",
        "what is the meaning",
        "explain the concept",
        "what is ",
    ]

    if any(
        pattern in q
        for pattern in definition_patterns
    ):
        return "definition"

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    statistical_words = [
        "rate",
        "percentage",
        "percent",
        "%",
        "total",
        "number",
        "how many",
        "value",
        "amount",
        "average",
        "mean",
        "median",
        "maximum",
        "minimum",
        "highest",
        "lowest",
        "population",
        "employment",
        "unemployment",
        "inflation",
        "cpi",
        "index",
        "growth",
        "change",
        "increase",
        "decrease",
        "trend",
    ]

    if any(
        word in q
        for word in statistical_words
    ):
        return "statistics"

    return "general"


# ============================================================
# GREETING DETECTION
# ============================================================

def is_greeting(question: str) -> bool:

    q = question.lower().strip()

    greetings = {
        "hi",
        "hello",
        "hey",
        "hey there",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
        "what's up",
        "whats up",
        "sup",
    }

    return q in greetings


# ============================================================
# UPLOAD REFERENCE DETECTION
# ============================================================

def detect_upload_reference(
    question: str,
    metadata: dict
) -> bool:

    question_lower = question.lower().strip()

    # --------------------------------------------------------
    # IMPORTANT
    #
    # file_id is the reliable indicator that this is an
    # uploaded document.
    # --------------------------------------------------------

    if not metadata.get("file_id"):
        return False

    # --------------------------------------------------------
    # Get document name
    # --------------------------------------------------------

    document_name = str(
        metadata.get(
            "document",
            metadata.get(
                "filename",
                metadata.get(
                    "source",
                    ""
                )
            )
        )
    ).lower()

    # --------------------------------------------------------
    # Filename matching
    # --------------------------------------------------------

    filename_words = [
        word
        for word in re.findall(
            r"[a-z0-9]+",
            document_name
        )
        if len(word) > 3
    ]

    matches = sum(
        1
        for word in filename_words
        if word in question_lower
    )

    if matches >= 2:
        return True

    # --------------------------------------------------------
    # Explicit references
    # --------------------------------------------------------

    upload_words = [
        "uploaded",
        "upload",
        "this report",
        "the report",
        "this file",
        "the file",
        "this document",
        "the document",
        "attached report",
        "attached file",
        "attached document",
    ]

    if any(
        word in question_lower
        for word in upload_words
    ):
        return True

    return False


# ============================================================
# REPORT PERIOD EXTRACTION
# ============================================================

def extract_report_period(question: str):

    q = question.lower()

    # --------------------------------------------------------
    # Months
    # --------------------------------------------------------

    months = [
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    ]

    month = None

    for m in months:

        if m in q:

            month = m
            break

    # --------------------------------------------------------
    # EFY / Gregorian year
    #
    # Examples:
    #
    # 2017
    # EFY 2017
    # efy 2017
    # year 2017
    # --------------------------------------------------------

    year_match = re.search(
        r"(?:efy\s*)?20\d{2}",
        q
    )

    year = None

    if year_match:

        year = year_match.group(0)

    return month, year


# ============================================================
# RERANK SCORE
# ============================================================

def rerank_score(
    question: str,
    text: str,
    distance: float,
    metadata: dict | None = None
) -> float:

    text_lower = text.lower()

    # --------------------------------------------------------
    # Detect question intent
    # --------------------------------------------------------

    intent = detect_question_intent(
        question
    )

    # --------------------------------------------------------
    # Base similarity
    #
    # Chroma distance:
    # lower = better
    # --------------------------------------------------------

    score = (
        1 - distance
    ) * 100

    # ========================================================
    # GREETING
    # ========================================================

    if intent == "greeting":

        return -1000

    # ========================================================
    # REPORT PERIOD MATCHING
    # ========================================================

    requested_month, requested_year = (
        extract_report_period(question)
    )

    if requested_month or requested_year:

        # ----------------------------------------------------
        # Get document name from metadata
        # ----------------------------------------------------

        document_name = ""

        if metadata:

            document_name = str(
                metadata.get(
                    "document",
                    metadata.get(
                        "filename",
                        metadata.get(
                            "source",
                            ""
                        )
                    )
                )
            ).lower()

        # ----------------------------------------------------
        # Combine document name + chunk text
        # ----------------------------------------------------

        period_text = (
            document_name
            + " "
            + text_lower
        )

        # ----------------------------------------------------
        # MONTH MATCH
        # ----------------------------------------------------

        month_match = False

        if requested_month:

            month_match = (
                requested_month.lower()
                in period_text
            )

        # ----------------------------------------------------
        # YEAR MATCH
        # ----------------------------------------------------

        year_match = False

        if requested_year:

            year_digits = re.search(
                r"20\d{2}",
                requested_year
            )

            if year_digits:

                year_value = (
                    year_digits.group(0)
                )

                year_match = (
                    year_value
                    in period_text
                )

        # ----------------------------------------------------
        # EXACT MONTH + YEAR MATCH
        #
        # Example:
        #
        # June EFY 2017
        #
        # June + 2017
        #
        # Strong bonus.
        # ----------------------------------------------------

        if (
            requested_month
            and requested_year
            and month_match
            and year_match
        ):

            score += 30

        # ----------------------------------------------------
        # MONTH ONLY MATCH
        # ----------------------------------------------------

        elif (
            requested_month
            and month_match
        ):

            score += 8

        # ----------------------------------------------------
        # YEAR ONLY MATCH
        # ----------------------------------------------------

        elif (
            requested_year
            and year_match
        ):

            score += 8

    # ========================================================
    # SUMMARY
    # ========================================================

    if intent == "summary":

        summary_words = [
            "summary",
            "overview",
            "main findings",
            "key findings",
            "conclusion",
            "introduction",
            "report",
            "finding",
            "inflation",
            "cpi",
        ]

        # ----------------------------------------------------
        # Summary keyword bonus
        # ----------------------------------------------------

        for word in summary_words:

            if word in text_lower:

                score += 8

        # ----------------------------------------------------
        # Tables can contain useful information
        # ----------------------------------------------------

        if "table" in text_lower:

            score += 2

        # ----------------------------------------------------
        # Longer chunks provide broader context
        # ----------------------------------------------------

        if len(text) > 500:

            score += 3

        if len(text) > 800:

            score += 2

    # ========================================================
    # STATISTICS
    # ========================================================

    elif intent == "statistics":

        # ----------------------------------------------------
        # Table bonus
        # ----------------------------------------------------

        if "table" in text_lower:

            score += 8

        # ----------------------------------------------------
        # Percentage bonus
        # ----------------------------------------------------

        if "%" in text:

            score += 5

        if "percent" in text_lower:

            score += 5

        # ----------------------------------------------------
        # Statistical keywords
        # ----------------------------------------------------

        if any(
            word in text_lower
            for word in [
                "total",
                "male",
                "female",
                "urban",
                "rural",
                "country",
            ]
        ):

            score += 4

        # ----------------------------------------------------
        # Number-rich chunks
        # ----------------------------------------------------

        numbers = re.findall(
            r"\d+(?:\.\d+)?",
            text
        )

        if len(numbers) >= 5:

            score += 3

    # ========================================================
    # DEFINITION
    # ========================================================

    elif intent == "definition":

        definition_words = [
            "defined as",
            "definition",
            "refers to",
            "means",
            "is defined",
            "is calculated",
            "is computed",
        ]

        # ----------------------------------------------------
        # Definition keyword bonus
        # ----------------------------------------------------

        if any(
            word in text_lower
            for word in definition_words
        ):

            score += 15

        # ----------------------------------------------------
        # Tables are usually less useful for definitions
        # ----------------------------------------------------

        if "table" in text_lower:

            score -= 5

    # ========================================================
    # UPLOADED FILE
    # ========================================================

    if metadata:

        if detect_upload_reference(
            question,
            metadata
        ):

            score += 40

    # ========================================================
    # FINAL SCORE
    # ========================================================

    return round(
        score,
        2
    )


# ============================================================
# RETRIEVER
# ============================================================

class Retriever:

    def __init__(self):

        self.embedder = EmbeddingService()

        self.store = VectorStore()

        # ----------------------------------------------------
        # Normal Chroma distance threshold
        #
        # Lower distance = better match.
        # ----------------------------------------------------

        self.distance_threshold = 1.0

        # ----------------------------------------------------
        # Uploaded summary threshold
        #
        # Uploaded summaries are restricted by file_id,
        # so we can safely allow a larger distance.
        # ----------------------------------------------------

        self.upload_summary_distance_threshold = 2.0

    # ========================================================
    # FILE EXISTENCE CHECK
    # ========================================================

    def file_exists(
        self,
        file_id: str
    ) -> bool:

        if not file_id:

            return False

        try:

            results = (
                self.store.collection.get(
                    where={
                        "file_id": file_id
                    },
                    limit=1,
                    include=[
                        "metadatas"
                    ]
                )
            )

            metadatas = results.get(
                "metadatas",
                []
            )

            return len(metadatas) > 0

        except Exception as e:

            print(
                "❌ File existence check failed:"
            )

            print(e)

            return False

    # ========================================================
    # SEARCH
    # ========================================================

    def search(
        self,
        question: str,
        file_id: str | None = None,
        n_results: int = 6,
        candidate_results: int = 20
    ):

        question = question.strip()

        # ====================================================
        # EMPTY QUESTION
        # ====================================================

        if not question:

            print(
                "⚠️ Empty question."
            )

            return []

        # ====================================================
        # GREETING
        # ====================================================

        if is_greeting(question):

            print(
                "👋 Greeting detected."
            )

            print(
                "🚫 RAG search skipped."
            )

            return []

        # ====================================================
        # INTENT
        # ====================================================

        intent = detect_question_intent(
            question
        )

        print(
            f"\nQuestion intent: {intent}"
        )

        # ====================================================
        # FILE MODE
        # ====================================================

        if file_id:

            print(
                "\n📎 FILE-SPECIFIC SEARCH"
            )

            print(
                "File ID:",
                file_id
            )

            # ------------------------------------------------
            # Make sure uploaded file exists
            # ------------------------------------------------

            if not self.file_exists(
                file_id
            ):

                print(
                    "❌ Uploaded file was not found in Chroma."
                )

                return []

        else:

            print(
                "\n🌍 ESS-WIDE SEARCH"
            )

        # ====================================================
        # CREATE EMBEDDING
        # ====================================================

        try:

            embedding = (
                self.embedder
                .encode(question)
                .tolist()
            )

        except Exception as e:

            print(
                "❌ Embedding failed:"
            )

            print(e)

            return []

        # ====================================================
        # CHROMA QUERY
        # ====================================================

        query_kwargs = {

            "query_embeddings": [
                embedding
            ],

            "n_results": candidate_results,
        }

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # If file_id exists, ONLY search that uploaded file.
        # ----------------------------------------------------

        if file_id:

            query_kwargs["where"] = {
                "file_id": file_id
            }

        # ====================================================
        # RUN CHROMA
        # ====================================================

        try:

            results = (
                self.store.collection.query(
                    **query_kwargs
                )
            )

        except Exception as e:

            print(
                "❌ Chroma search failed:"
            )

            print(e)

            return []

        # ====================================================
        # EMPTY RESULTS
        # ====================================================

        if not results:

            print(
                "⚠️ Chroma returned no results."
            )

            return []

        documents = (
            results.get(
                "documents",
                [[]]
            )[0]
        )

        metadatas = (
            results.get(
                "metadatas",
                [[]]
            )[0]
        )

        distances = (
            results.get(
                "distances",
                [[]]
            )[0]
        )

        # ====================================================
        # PROCESS RESULTS
        # ====================================================

        output = []

        print(
            "\n" + "=" * 80
        )

        print(
            "RETRIEVER RESULTS"
        )

        print(
            "=" * 80
        )

        # ====================================================
        # UPLOADED SUMMARY MODE
        # ====================================================

        uploaded_summary_mode = (
            file_id is not None
            and intent == "summary"
        )

        if uploaded_summary_mode:

            print(
                "\n📝 UPLOADED PDF SUMMARY MODE"
            )

            print(
                "Normal distance threshold:",
                self.distance_threshold
            )

            print(
                "Summary distance threshold:",
                self.upload_summary_distance_threshold
            )

            print(
                "All accepted chunks are restricted to file_id:",
                file_id
            )

        # ====================================================
        # PROCESS CHROMA RESULTS
        # ====================================================

        for index, (
            doc,
            meta,
            distance
        ) in enumerate(
            zip(
                documents,
                metadatas,
                distances
            ),
            start=1
        ):

            # ------------------------------------------------
            # Ignore empty documents
            # ------------------------------------------------

            if not doc:

                continue

            meta = meta or {}

            # ------------------------------------------------
            # Metadata
            # ------------------------------------------------

            document_name = meta.get(
                "document",
                "Unknown document"
            )

            category = meta.get(
                "category",
                "PDF"
            )

            page = meta.get(
                "page",
                None
            )

            result_file_id = meta.get(
                "file_id"
            )

            # ------------------------------------------------
            # Debug information
            # ------------------------------------------------

            print(
                f"\nChunk #{index}"
            )

            print(
                "-" * 80
            )

            print(
                "Document:",
                document_name
            )

            print(
                "Category:",
                category
            )

            print(
                "Page:",
                page
            )

            print(
                "File ID:",
                result_file_id
            )

            print(
                f"Distance: {distance:.4f}"
            )

            # =================================================
            # FILE SAFETY
            # =================================================

            if file_id:

                if result_file_id != file_id:

                    print(
                        "❌ WRONG FILE — REJECTED"
                    )

                    continue

            # =================================================
            # DISTANCE FILTER
            # =================================================

            # -------------------------------------------------
            # Uploaded summary mode
            # -------------------------------------------------

            if uploaded_summary_mode:

                if (
                    distance
                    > self.upload_summary_distance_threshold
                ):

                    print(
                        "❌ Rejected:"
                        f" distance > "
                        f"{self.upload_summary_distance_threshold}"
                    )

                    continue

                print(
                    "✅ Accepted for uploaded summary"
                )

            # -------------------------------------------------
            # Normal mode
            # -------------------------------------------------

            else:

                if distance > self.distance_threshold:

                    print(
                        "❌ Rejected:"
                        f" distance > "
                        f"{self.distance_threshold}"
                    )

                    continue

                print(
                    "✅ Accepted"
                )

            # =================================================
            # EXTRACT BEST PARAGRAPH
            # =================================================

            try:

                best_paragraph = (
                    extract_best_paragraph(
                        doc,
                        question
                    )
                )

            except Exception as e:

                print(
                    "⚠️ Paragraph extraction failed:"
                )

                print(e)

                best_paragraph = doc

            if not best_paragraph:

                best_paragraph = doc

            # =================================================
            # RERANK
            # =================================================

            score = rerank_score(
                question,
                best_paragraph,
                distance,
                meta
            )

            # -------------------------------------------------
            # Uploaded summaries need broader context.
            # -------------------------------------------------

            if uploaded_summary_mode:

                if len(best_paragraph) >= 500:

                    score += 5

                if len(best_paragraph) >= 800:

                    score += 5

            score = round(
                score,
                2
            )

            # =================================================
            # SIMILARITY
            # =================================================

            similarity = (
                1 - distance
            ) * 100

            print(
                f"Similarity: "
                f"{similarity:.2f}"
            )

            print(
                f"Rank Score: "
                f"{score:.2f}"
            )

            # =================================================
            # ADD RESULT
            # =================================================

            output.append({

                "text": best_paragraph,

                "document": document_name,

                "category": category,

                "page": page,

                "path": meta.get(
                    "path",
                    ""
                ),

                "file_id": result_file_id,

                "distance": distance,

                "score": score,
            })

        # ====================================================
        # SORT
        # ====================================================

        output.sort(
            key=lambda item: (
                -item["score"],
                item["distance"]
            )
        )

        # ====================================================
        # LIMIT RESULTS
        # ====================================================

        if uploaded_summary_mode:

            # ------------------------------------------------
            # Summary gets more chunks.
            #
            # Minimum target = 10
            # But never exceed available results.
            # ------------------------------------------------

            summary_limit = min(
                max(n_results, 10),
                len(output)
            )

            output = output[
                :summary_limit
            ]

        else:

            output = output[
                :n_results
            ]

        # ====================================================
        # FINAL LOG
        # ====================================================

        print(
            "\n" + "=" * 80
        )

        print(
            "✅ Relevant results returned:",
            len(output)
        )

        print(
            "\nDocuments passed to Ollama:"
        )

        for i, item in enumerate(
            output,
            start=1
        ):

            print(
                f"{i}. "
                f"{item['document']} "
                f"(score={item['score']}, "
                f"distance={item['distance']:.4f})"
            )

            if item.get("page"):

                print(
                    "   Page:",
                    item["page"]
                )

            if item.get("file_id"):

                print(
                    "   File ID:",
                    item["file_id"]
                )

        print(
            "=" * 80
        )

        return output