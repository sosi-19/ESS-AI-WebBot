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

    if any(pattern in q for pattern in summary_patterns):
        return "summary"

    # ========================================================
    # COMPARISON
    # ========================================================
    #
    # IMPORTANT:
    # Comparison MUST be checked BEFORE definition.
    #
    # Example:
    # "What is the difference between employed and unemployed?"
    #
    # This should return:
    # comparison
    #
    # NOT:
    # definition
    # ========================================================

    comparison_patterns = [
        "difference between",
        "difference among",
        "difference of",
        "distinction between",
        "distinction among",
        "compare ",
        "compare the",
        "comparison between",
        "comparison of",
        "versus",
        " vs ",
        " vs.",
        "how is",
        "how are",
        "different from",
        "different than",
    ]

    if any(pattern in q for pattern in comparison_patterns):
        return "comparison"

    # --------------------------------------------------------
    # Definition
    # --------------------------------------------------------

    definition_patterns = [
        "define ",
        "definition",
        "definition of",
        "meaning of",
        "what does",
        "what is the meaning",
        "what is ",
        "what are ",
        "who are ",
        "explain the concept",
        "explain what",
        "refers to",
        "means",
    ]

    if any(pattern in q for pattern in definition_patterns):
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

    if any(word in q for word in statistical_words):
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

    if not metadata.get("file_id"):
        return False

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
    # Detect normal years such as 2021, 2022, 2023
    # Also supports EFY 2018 style wording.
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
# WORD HELPERS
# ============================================================

def contains_word(text: str, word: str) -> bool:

    return bool(
        re.search(
            rf"\b{re.escape(word)}\b",
            text.lower()
        )
    )


def contains_any_word(
    text: str,
    words: list[str]
) -> bool:

    text_lower = text.lower()

    return any(
        contains_word(
            text_lower,
            word
        )
        for word in words
    )


# ============================================================
# DEFINITION KEYWORD SCORING
# ============================================================

def definition_keyword_score(
    question: str,
    text: str
) -> float:

    q = question.lower()
    t = text.lower()

    score = 0.0

    # --------------------------------------------------------
    # Strong ESS-style definition phrases
    # --------------------------------------------------------

    strong_definition_phrases = [
        "defined as",
        "is defined as",
        "are defined as",
        "definition of",
        "definition for",
        "refers to",
        "refers to persons",
        "consists of persons",
        "consist of persons",
        "persons who",
        "persons aged",
        "population consists of",
        "population is defined",
        "population are defined",
        "means persons",
        "includes persons",
        "those persons who",
    ]

    for phrase in strong_definition_phrases:

        if phrase in t:
            score += 12

    # --------------------------------------------------------
    # Employment-specific definition phrases
    # --------------------------------------------------------

    employment_definition_phrases = [
        "employed population consists of",
        "employed persons who",
        "employed persons are",
        "employed population is",
        "employed population are",
        "definition of employment",
        "definition of employed",
        "currently employed persons",
        "currently employed population",
        "productive activity or work",
        "work at least for one hour",
        "worked at least one hour",
        "seven days prior",
        "reference week",
    ]

    for phrase in employment_definition_phrases:

        if phrase in t:
            score += 20

    # --------------------------------------------------------
    # Unemployment-specific definition phrases
    # --------------------------------------------------------

    unemployment_definition_phrases = [
        "definition of unemployment",
        "definition of unemployed",
        "unemployed population consists of",
        "unemployed persons who",
        "unemployed persons are",
        "measurement of unemployment",
        "without work",
        "available for work",
        "seeking work",
        "ready to take a job",
        "no job but available to work",
        "had no work but were available",
        "relaxed definition of unemployment",
        "standard definition of unemployment",
    ]

    for phrase in unemployment_definition_phrases:

        if phrase in t:
            score += 20

    # --------------------------------------------------------
    # If question explicitly asks about employment
    # --------------------------------------------------------

    if (
        contains_word(q, "employed")
        or contains_word(q, "employment")
    ):

        if (
            contains_word(t, "employed")
            or contains_word(t, "employment")
        ):
            score += 8

    # --------------------------------------------------------
    # If question explicitly asks about unemployment
    # --------------------------------------------------------

    if (
        contains_word(q, "unemployed")
        or contains_word(q, "unemployment")
    ):

        if (
            contains_word(t, "unemployed")
            or contains_word(t, "unemployment")
        ):
            score += 8

    # ========================================================
    # COMPARISON QUESTIONS
    # ========================================================

    comparison_question = any(
        phrase in q
        for phrase in [
            "difference between",
            "difference among",
            "difference of",
            "distinction between",
            "distinction among",
            "compare ",
            "comparison between",
            "comparison of",
            "versus",
            " vs ",
            " vs.",
            "different from",
            "different than",
        ]
    )

    if comparison_question:

        # ----------------------------------------------------
        # IMPORTANT:
        # Use word boundaries.
        #
        # "employed" should NOT match "unemployed".
        # ----------------------------------------------------

        has_employed = (
            contains_word(
                t,
                "employed"
            )
            or contains_word(
                t,
                "employment"
            )
        )

        has_unemployed = (
            contains_word(
                t,
                "unemployed"
            )
            or contains_word(
                t,
                "unemployment"
            )
        )

        if has_employed:
            score += 12

        if has_unemployed:
            score += 12

        # ----------------------------------------------------
        # Strong bonus when BOTH concepts occur.
        # ----------------------------------------------------

        if has_employed and has_unemployed:
            score += 20

        # ----------------------------------------------------
        # Additional ESS unemployment criteria.
        # ----------------------------------------------------

        if "without work" in t:
            score += 8

        if "available for work" in t:
            score += 8

        if "seeking work" in t:
            score += 8

        # ----------------------------------------------------
        # Additional employment criteria.
        # ----------------------------------------------------

        employment_phrases = [
            "productive activity",
            "economic activity",
            "worked at least",
            "work at least",
            "reference week",
            "reference period",
            "paid employment",
            "self employment",
            "own account",
        ]

        for phrase in employment_phrases:

            if phrase in t:
                score += 8

    # --------------------------------------------------------
    # Definition questions prefer text-heavy chunks
    # --------------------------------------------------------

    if len(text) >= 300:
        score += 2

    if len(text) >= 600:
        score += 2

    return score


# ============================================================
# COMPARISON KEYWORD SCORING
# ============================================================

def comparison_keyword_score(
    question: str,
    text: str
) -> float:

    q = question.lower()
    t = text.lower()

    score = 0.0

    comparison_question = any(
        phrase in q
        for phrase in [
            "difference between",
            "difference among",
            "difference of",
            "distinction between",
            "distinction among",
            "compare ",
            "comparison between",
            "comparison of",
            "versus",
            " vs ",
            " vs.",
            "different from",
            "different than",
        ]
    )

    if not comparison_question:
        return score

    # --------------------------------------------------------
    # Employment concept
    # --------------------------------------------------------

    has_employed = (
        contains_word(t, "employed")
        or contains_word(t, "employment")
    )

    has_unemployed = (
        contains_word(t, "unemployed")
        or contains_word(t, "unemployment")
    )

    if has_employed:
        score += 20

    if has_unemployed:
        score += 20

    # --------------------------------------------------------
    # BEST CASE:
    # Same chunk contains both concepts.
    # --------------------------------------------------------

    if has_employed and has_unemployed:
        score += 30

    # --------------------------------------------------------
    # Employment-related evidence
    # --------------------------------------------------------

    employment_phrases = [
        "productive activity",
        "economic activity",
        "worked",
        "work",
        "working",
        "paid employment",
        "self employment",
        "own account",
        "reference week",
        "reference period",
    ]

    for phrase in employment_phrases:

        if phrase in t:
            score += 5

    # --------------------------------------------------------
    # Unemployment-related evidence
    # --------------------------------------------------------

    unemployment_phrases = [
        "without work",
        "available for work",
        "seeking work",
        "looking for work",
        "ready to take a job",
        "no job but available",
        "standard definition",
        "relaxed definition",
    ]

    for phrase in unemployment_phrases:

        if phrase in t:
            score += 5

    # --------------------------------------------------------
    # Definition language
    # --------------------------------------------------------

    definition_phrases = [
        "defined as",
        "definition of",
        "refers to",
        "consists of persons",
        "persons who",
        "population consists",
    ]

    for phrase in definition_phrases:

        if phrase in t:
            score += 6

    return score


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

    intent = detect_question_intent(
        question
    )

    # --------------------------------------------------------
    # Base similarity
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
    # REPORT PERIOD
    # ========================================================

    requested_month, requested_year = (
        extract_report_period(question)
    )

    if requested_month or requested_year:

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

        period_text = (
            document_name
            + " "
            + text_lower
        )

        month_match = False

        if requested_month:

            month_match = (
                requested_month.lower()
                in period_text
            )

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

        if (
            requested_month
            and requested_year
            and month_match
            and year_match
        ):

            score += 30

        elif (
            requested_month
            and month_match
        ):

            score += 8

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

        for word in summary_words:

            if word in text_lower:
                score += 8

        if "table" in text_lower:
            score += 2

        if len(text) > 500:
            score += 3

        if len(text) > 800:
            score += 2

    # ========================================================
    # STATISTICS
    # ========================================================

    elif intent == "statistics":

        if "table" in text_lower:
            score += 8

        if "%" in text:
            score += 5

        if "percent" in text_lower:
            score += 5

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

        score += definition_keyword_score(
            question,
            text
        )

        # ----------------------------------------------------
        # Definitions are usually prose, not tables.
        # ----------------------------------------------------

        if "table" in text_lower:
            score -= 5

        # ----------------------------------------------------
        # Strong penalty for purely numerical chunks.
        # ----------------------------------------------------

        numbers = re.findall(
            r"\d+(?:\.\d+)?",
            text
        )

        if len(numbers) >= 10:
            score -= 3

    # ========================================================
    # COMPARISON
    # ========================================================

    elif intent == "comparison":

        score += comparison_keyword_score(
            question,
            text
        )

        # ----------------------------------------------------
        # Comparison questions should prefer explanatory
        # prose instead of large numerical tables.
        # ----------------------------------------------------

        if "table" in text_lower:
            score -= 3

        numbers = re.findall(
            r"\d+(?:\.\d+)?",
            text
        )

        if len(numbers) >= 15:
            score -= 3

    # ========================================================
    # UPLOADED FILE
    # ========================================================

    if metadata:

        if detect_upload_reference(
            question,
            metadata
        ):
            score += 40

    return round(
        score,
        2
    )


# ============================================================
# RETRIEVER
# ============================================================

class Retriever:

    def __init__(self):

        print(
            "\nInitializing ESS Retriever..."
        )

        self.embedder = EmbeddingService()

        self.store = VectorStore()

        # ----------------------------------------------------
        # Normal Chroma distance threshold
        # ----------------------------------------------------

        self.distance_threshold = 1.0

        # ----------------------------------------------------
        # Uploaded summary threshold
        # ----------------------------------------------------

        self.upload_summary_distance_threshold = 2.0

        print(
            "ESS Retriever initialized."
        )

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
                "File existence check failed:"
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
                "Empty question."
            )

            return []

        # ====================================================
        # GREETING
        # ====================================================

        if is_greeting(question):

            print(
                "Greeting detected."
            )

            print(
                "RAG search skipped."
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
        # DEFINITION / COMPARISON QUESTIONS
        # ====================================================

        effective_candidate_results = (
            candidate_results
        )

        # ----------------------------------------------------
        # Both definition and comparison questions can have
        # their evidence split across adjacent chunks.
        # ----------------------------------------------------

        if intent in (
            "definition",
            "comparison"
        ):

            effective_candidate_results = max(
                candidate_results,
                50
            )

            print(
                f"{intent.capitalize()} search: "
                f"expanding candidates "
                f"from {candidate_results} to "
                f"{effective_candidate_results}"
            )

        # ====================================================
        # FILE MODE
        # ====================================================

        if file_id:

            print(
                "\nFILE-SPECIFIC SEARCH"
            )

            print(
                "File ID:",
                file_id
            )

            if not self.file_exists(
                file_id
            ):

                print(
                    "Uploaded file was not found in Chroma."
                )

                return []

        else:

            print(
                "\nESS-WIDE SEARCH"
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
                "Embedding failed:"
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

            "n_results":
                effective_candidate_results,
        }

        # ----------------------------------------------------
        # Uploaded PDF = ONLY that file
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
                "Chroma search failed:"
            )

            print(e)

            return []

        # ====================================================
        # EMPTY RESULTS
        # ====================================================

        if not results:

            print(
                "Chroma returned no results."
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
                "\nUPLOADED PDF SUMMARY MODE"
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

            if not doc:
                continue

            meta = meta or {}

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
                        "WRONG FILE — REJECTED"
                    )

                    continue

            # =================================================
            # DISTANCE FILTER
            # =================================================

            if uploaded_summary_mode:

                if (
                    distance
                    > self.upload_summary_distance_threshold
                ):

                    print(
                        "Rejected:"
                        f" distance > "
                        f"{self.upload_summary_distance_threshold}"
                    )

                    continue

                print(
                    "Accepted for uploaded summary"
                )

            else:

                if distance > self.distance_threshold:

                    print(
                        "Rejected:"
                        f" distance > "
                        f"{self.distance_threshold}"
                    )

                    continue

                print(
                    "Accepted"
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
                    "Paragraph extraction failed:"
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

                "text":
                    best_paragraph,

                "document":
                    document_name,

                "category":
                    category,

                "page":
                    page,

                "path":
                    meta.get(
                        "path",
                        ""
                    ),

                "file_id":
                    result_file_id,

                "distance":
                    distance,

                "score":
                    score,
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
            "Relevant results returned:",
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