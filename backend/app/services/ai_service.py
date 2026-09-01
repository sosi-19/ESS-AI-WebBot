
import os
import time
import requests

from app.rag.retriever import Retriever
from app.services.csv_ai_service import csv_ai_service


# ============================================================
# OLLAMA CONFIGURATION
# ============================================================

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:1.5b"
)


# ============================================================
# RETRIEVER
# ============================================================

retriever = Retriever()


# ============================================================
# AI RESPONSE CACHE
# ============================================================

AI_CACHE = {}

CACHE_TTL = 3600
CACHE_MAX_SIZE = 100


# ============================================================
# NORMALIZE QUESTION
# ============================================================

def normalize_question(message: str) -> str:
    """
    Normalize a user question for comparison/cache purposes.
    """

    if not message:
        return ""

    return " ".join(
        message.lower().strip().split()
    )


# ============================================================
# CACHE KEY
# ============================================================

def make_cache_key(
    message: str,
    file_id: str | None = None
):
    """
    Create a cache key.

    Uploaded PDF questions are isolated by file_id.
    """

    question = normalize_question(message)

    if file_id:
        return f"FILE:{file_id}::{question}"

    return f"ESS::{question}"


# ============================================================
# CACHE GET
# ============================================================

def get_cached_response(
    message: str,
    file_id: str | None = None
):

    key = make_cache_key(
        message,
        file_id
    )

    cached = AI_CACHE.get(key)

    if cached is None:
        return None

    # Check expiration
    if (
        time.time()
        - cached["timestamp"]
        > CACHE_TTL
    ):

        del AI_CACHE[key]

        print("🗑️ Cache expired")

        return None

    print("⚡ CACHE HIT")

    return cached["result"]


# ============================================================
# CACHE SAVE
# ============================================================

def save_cached_response(
    message: str,
    result: dict,
    file_id: str | None = None
):

    key = make_cache_key(
        message,
        file_id
    )

    # Remove oldest item if cache is full
    if len(AI_CACHE) >= CACHE_MAX_SIZE:

        oldest_key = next(
            iter(AI_CACHE)
        )

        del AI_CACHE[oldest_key]

    AI_CACHE[key] = {

        "result": result,

        "timestamp": time.time()

    }

    print("💾 Response saved to cache")


# ============================================================
# GREETING DETECTION
# ============================================================

def is_greeting(question: str):

    question = normalize_question(
        question
    )

    greetings = {

        "hi",
        "hello",
        "hey",
        "hiya",
        "hey there",
        "hello there",

        "good morning",
        "good afternoon",
        "good evening",

        "selam",
        "salam",

        "ሰላም",
        "ሀይ",
        "ሃይ",
        "ሂ"

    }

    return question in greetings


# ============================================================
# GREETING RESPONSE
# ============================================================

def greeting_response():

    return {

        "answer": (
            "Hello! 👋 Welcome to the "
            "Ethiopia Statistical Service (ESS) AI Assistant. "
            "How can I help you today?"
        ),

        "sources": [],

        "type": "greeting"

    }


# ============================================================
# SOURCE DETECTION
# ============================================================

def detect_source(question: str):

    question = normalize_question(
        question
    )

    # --------------------------------------------------------
    # CSV DATASET SIGNALS
    # --------------------------------------------------------

    csv_dataset_keywords = [

        "dataset",
        "datasets",
        "csv",
        "record",
        "records",
        "row",
        "rows",
        "column",
        "columns",

        "agriculture dataset",
        "education dataset",
        "health dataset",
        "roster dataset"

    ]

    # --------------------------------------------------------
    # CSV OPERATION SIGNALS
    # --------------------------------------------------------

    csv_operation_keywords = [

        "average",
        "mean",
        "maximum",
        "minimum",
        "max",
        "min",
        "median",
        "unique",

        "standard deviation",
        "variance",
        "quartile",
        "percentile",
        "correlation"

    ]

    # --------------------------------------------------------
    # PDF SIGNALS
    # --------------------------------------------------------

    pdf_keywords = [

        "report",
        "reports",

        "survey",
        "surveys",

        "document",
        "documents",

        "pdf",

        "according to",
        "according",

        "findings",
        "key findings",

        "statistical report",
        "study",

        "summarize",
        "summarise",
        "summary",

        "overview",
        "main points",
        "key points"

    ]

    has_csv_dataset_signal = any(
        keyword in question
        for keyword in csv_dataset_keywords
    )

    has_csv_operation_signal = any(
        keyword in question
        for keyword in csv_operation_keywords
    )

    has_pdf_signal = any(
        keyword in question
        for keyword in pdf_keywords
    )

    csv_dataset_names = [

        "agriculture",
        "education",
        "health",
        "roster"

    ]

    has_csv_dataset_name = any(
        dataset in question
        for dataset in csv_dataset_names
    )

    return {

        "csv_dataset":
            has_csv_dataset_signal,

        "csv_operation":
            has_csv_operation_signal,

        "csv_name":
            has_csv_dataset_name,

        "pdf":
            has_pdf_signal

    }


# ============================================================
# BUILD PDF CONTEXT
# ============================================================

def build_pdf_context(results):

    context_parts = []

    for index, item in enumerate(
        results,
        start=1
    ):

        document = item.get(
            "document",
            "Unknown document"
        )

        category = item.get(
            "category",
            "PDF"
        )

        page = item.get(
            "page",
            "Unknown"
        )

        text = item.get(
            "text",
            ""
        )

        if not text or not text.strip():
            continue

        context_parts.append(

            f"Evidence {index}\n"
            f"Document: {document}\n"
            f"Category: {category}\n"
            f"Page: {page}\n"
            f"Content:\n{text}"

        )

    return "\n\n========================\n\n".join(
        context_parts
    )


# ============================================================
# BUILD PDF SOURCES
# ============================================================

def build_pdf_sources(results):

    sources = []

    seen = set()

    for item in results:

        document = item.get(
            "document"
        )

        if not document:
            continue

        page = item.get(
            "page"
        )

        source_key = (
            document,
            page
        )

        if source_key in seen:
            continue

        source = {

            "document":
                document,

            "category":
                item.get(
                    "category",
                    "PDF"
                ),

            "page":
                page

        }

        if item.get("file_id"):

            source["file_id"] = item.get(
                "file_id"
            )

        sources.append(
            source
        )

        seen.add(
            source_key
        )

    return sources


# ============================================================
# PDF PROMPT
# ============================================================

def build_pdf_prompt(
    message: str,
    context: str,
    uploaded: bool = False
):

    if uploaded:

        source_description = (
            "The evidence below comes ONLY from "
            "the PDF uploaded by the user."
        )

        missing_message = (
            "The information was not found in the uploaded PDF."
        )

    else:

        source_description = (
            "The evidence below comes from "
            "ESS PDF documents."
        )

        missing_message = (
            "The information was not found in "
            "the provided ESS documents."
        )

    return f"""
You are the Ethiopia Statistical Service (ESS) AI Assistant.

{source_description}

Your task is to answer the user's question using ONLY
the PDF evidence provided below.

IMPORTANT RULES:

1. Never use outside knowledge.
2. Never invent numbers, percentages, dates, names,
   locations, or statistics.
3. Never guess missing information.
4. If the user asks for a specific value, return the
   exact value found in the evidence.
5. If the user asks for a summary, summarize the important
   findings across the useful evidence.
6. For summaries, include important indicators, trends,
   increases, decreases, comparisons, and major findings.
7. Do not focus on only one table when several pieces of
   evidence are relevant.
8. Combine related evidence from multiple pages when useful.
9. Preserve the exact year and month.
10. Pay special attention to Ethiopian Fiscal Year (EFY).
11. Do not mix values from different periods.
12. If a value is explicitly stated in the evidence,
    use that exact value.
13. If useful, mention the page number.
14. Do not describe the retrieval process.
15. Do not mention RAG, embeddings, chunks, Chroma,
    vector databases, or Ollama.
16. Keep the answer clear and professional.
17. If the requested information is not present, say:

"{missing_message}"

18. For a summary, do not return the missing-information
    message simply because one small detail is absent.
19. Do not create information to make the answer longer.
20. If the evidence contains a table, carefully read the
    table before answering.
21. If several values appear, select the value that directly
    matches the user's requested indicator and period.
22. Never substitute a nearby month, year, or different
    inflation measure.
23. If the question asks "What was Ethiopia's inflation
    rate", clearly state the inflation rate and period.

============================================================
PDF EVIDENCE
============================================================

{context}

============================================================
USER QUESTION
============================================================

{message}

============================================================
ANSWER
============================================================
"""


# ============================================================
# HYBRID PROMPT
# ============================================================

def build_hybrid_prompt(
    message: str,
    csv_answer: str,
    pdf_context: str
):

    return f"""
You are the Ethiopia Statistical Service (ESS) AI Assistant.

Answer the user's question using ONLY the CSV result
and the retrieved ESS PDF evidence below.

IMPORTANT RULES:

1. Never use outside knowledge.
2. Never invent statistics.
3. Never guess missing values.
4. Clearly distinguish CSV information from PDF information.
5. Pay attention to:
   - year
   - EFY
   - survey round
   - sex
   - age group
   - geographic scope
   - indicator
6. If CSV and PDF contain different values,
   explain the difference.
7. Use exact values from the evidence.
8. Keep the answer concise and professional.

============================================================
CSV RESULT
============================================================

{csv_answer}

============================================================
PDF EVIDENCE
============================================================

{pdf_context}

============================================================
USER QUESTION
============================================================

{message}

============================================================
ANSWER
============================================================
"""


# ============================================================
# EMPTY PDF RESPONSE
# ============================================================

def no_pdf_information_response(
    uploaded: bool = False
):

    if uploaded:

        return (
            "The information was not found "
            "in the uploaded PDF."
        )

    return (
        "The information was not found "
        "in the provided ESS documents."
    )


# ============================================================
# OLLAMA NORMAL RESPONSE
# ============================================================

def ask_ollama(prompt: str):

    start_time = time.time()

    payload = {

        "model": MODEL,

        "prompt": prompt,

        "stream": False,

        "keep_alive": "30m",

        "options": {

            "temperature": 0.0,

            "num_predict": 300,

            "num_ctx": 4096,

            "top_k": 10,

            "top_p": 0.5

        }

    }

    print(
        "\nPROMPT CHARACTERS:",
        len(prompt)
    )

    try:

        response = requests.post(

            OLLAMA_URL,

            json=payload,

            timeout=120

        )

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.ConnectionError:

        print(
            "❌ Could not connect to Ollama."
        )

        return (
            "The AI service is currently unavailable. "
            "Please make sure Ollama is running."
        )

    except requests.exceptions.Timeout:

        print(
            "❌ Ollama request timed out."
        )

        return (
            "The AI response took too long. "
            "Please try again."
        )

    except requests.exceptions.RequestException as e:

        print(
            "❌ Ollama request failed:",
            e
        )

        return (
            "The AI service encountered an error. "
            "Please try again."
        )

    except Exception as e:

        print(
            "❌ Unexpected Ollama error:",
            e
        )

        return (
            "The AI service encountered an "
            "unexpected error."
        )

    answer = data.get(
        "response",
        ""
    )

    print(
        "Ollama total duration:",
        data.get(
            "total_duration",
            0
        ) / 1_000_000_000,
        "seconds"
    )

    print(
        "Ollama prompt tokens:",
        data.get(
            "prompt_eval_count",
            0
        )
    )

    print(
        "Ollama generated tokens:",
        data.get(
            "eval_count",
            0
        )
    )

    print(
        f"🤖 Python request time: "
        f"{time.time() - start_time:.2f} seconds"
    )

    return answer.strip()


# ============================================================
# OLLAMA STREAMING
# ============================================================

def stream_ollama(prompt: str):

    payload = {

        "model": MODEL,

        "prompt": prompt,

        "stream": True,

        "keep_alive": "30m",

        "options": {

            "temperature": 0.0,

            "num_predict": 300,

            "num_ctx": 4096,

            "top_k": 10,

            "top_p": 0.5

        }

    }

    print(
        "\n🌊 Starting Ollama stream..."
    )

    print(
        "Streaming prompt length:",
        len(prompt)
    )

    try:

        response = requests.post(

            OLLAMA_URL,

            json=payload,

            stream=True,

            timeout=120

        )

        response.raise_for_status()

    except requests.exceptions.ConnectionError:

        print(
            "❌ Could not connect to Ollama."
        )

        return

    except requests.exceptions.Timeout:

        print(
            "❌ Ollama streaming request timed out."
        )

        return

    except requests.exceptions.RequestException as e:

        print(
            "❌ Ollama streaming error:",
            e
        )

        return

    try:

        for line in response.iter_lines(
            decode_unicode=True
        ):

            if not line:
                continue

            # IMPORTANT:
            # Ollama returns one JSON object per line.
            #
            # We return the complete JSON line to the
            # FastAPI streaming endpoint.
            #
            # The frontend should parse the Ollama JSON
            # and use the "response" field.

            yield line

    finally:

        response.close()


# ============================================================
# UNCACHED AI ROUTER
# ============================================================

def _ask_ai_uncached(
    message: str,
    file_id: str | None = None
):

    total_start = time.time()

    question = normalize_question(
        message
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "🤖 AI REQUEST"
    )

    print(
        "QUESTION:",
        message
    )

    print(
        "FILE ID:",
        file_id
    )

    print(
        "=" * 70
    )

    # ========================================================
    # 1. GREETING
    # ========================================================

    if is_greeting(question):

        print(
            "\n👋 GREETING DETECTED"
        )

        print(
            "🚫 RAG SEARCH SKIPPED"
        )

        print(
            "🚫 CSV SEARCH SKIPPED"
        )

        return greeting_response()

    # ========================================================
    # 2. SOURCE DETECTION
    # ========================================================

    source = detect_source(
        question
    )

    print(
        "\n========== SOURCE DETECTION =========="
    )

    print(
        "CSV dataset:",
        source["csv_dataset"]
    )

    print(
        "CSV operation:",
        source["csv_operation"]
    )

    print(
        "CSV name:",
        source["csv_name"]
    )

    print(
        "PDF:",
        source["pdf"]
    )

    print(
        "======================================"
    )

    # ========================================================
    # 3. UPLOADED FILE MODE
    # ========================================================

    # IMPORTANT:
    #
    # file_id ALWAYS takes priority.
    #
    # Even if the question does not contain the word
    # "report" or "PDF", the presence of file_id means
    # the user is asking against the uploaded PDF.

    if file_id:

        print(
            "\n📎 UPLOADED FILE MODE"
        )

        print(
            "File ID:",
            file_id
        )

        pdf_start = time.time()

        try:

            results = retriever.search(

                message,

                file_id=file_id

            )

        except Exception as e:

            print(
                "❌ Uploaded PDF retrieval error:",
                e
            )

            return {

                "answer":
                    "There was an error reading "
                    "the uploaded PDF.",

                "sources": [],

                "type":
                    "pdf"

            }

        pdf_time = (
            time.time()
            - pdf_start
        )

        print(
            "📄 Uploaded PDF retrieval time:",
            round(
                pdf_time,
                2
            ),
            "seconds"
        )

        print(
            "📄 Retrieved chunks:",
            len(results)
        )

        if not results:

            print(
                "❌ No results found in uploaded file"
            )

            return {

                "answer":
                    no_pdf_information_response(
                        uploaded=True
                    ),

                "sources": [],

                "type":
                    "pdf"

            }

        # ----------------------------------------------------
        # Keep strongest results
        # ----------------------------------------------------

        top_results = results[:6]

        print(
            "📄 Chunks sent to Ollama:",
            len(top_results)
        )

        # ----------------------------------------------------
        # Build context
        # ----------------------------------------------------

        context = build_pdf_context(
            top_results
        )

        print(
            "Context length:",
            len(context)
        )

        if not context.strip():

            print(
                "❌ Uploaded PDF context is empty"
            )

            return {

                "answer":
                    no_pdf_information_response(
                        uploaded=True
                    ),

                "sources": [],

                "type":
                    "pdf"

            }

        # ----------------------------------------------------
        # Build prompt
        # ----------------------------------------------------

        prompt = build_pdf_prompt(

            message,

            context,

            uploaded=True

        )

        print(
            "Prompt length:",
            len(prompt)
        )

        # ----------------------------------------------------
        # Ask Ollama
        # ----------------------------------------------------

        ollama_start = time.time()

        answer = ask_ollama(
            prompt
        )

        print(
            "🤖 Uploaded PDF Ollama time:",
            round(
                time.time()
                - ollama_start,
                2
            ),
            "seconds"
        )

        # ----------------------------------------------------
        # Sources
        # ----------------------------------------------------

        sources = build_pdf_sources(
            top_results
        )

        total_time = (
            time.time()
            - total_start
        )

        print(
            "⏱️ Uploaded PDF AI time:",
            round(
                total_time,
                2
            ),
            "seconds"
        )

        return {

            "answer":
                answer,

            "sources":
                sources,

            "type":
                "pdf"

        }

    # ========================================================
    # 4. HYBRID CSV + PDF
    # ========================================================

    if (
        source["csv_dataset"]
        and source["pdf"]
    ):

        print(
            "\n🔀 HYBRID QUESTION DETECTED"
        )

        # ----------------------------------------------------
        # CSV
        # ----------------------------------------------------

        csv_start = time.time()

        csv_result = (
            csv_ai_service.answer(
                message
            )
        )

        csv_time = (
            time.time()
            - csv_start
        )

        print(
            "📊 CSV processing time:",
            round(
                csv_time,
                2
            ),
            "seconds"
        )

        csv_answer = csv_result.get(

            "answer",

            "No relevant CSV result was found."

        )

        # ----------------------------------------------------
        # PDF
        # ----------------------------------------------------

        pdf_start = time.time()

        pdf_results = retriever.search(
            message
        )

        pdf_time = (
            time.time()
            - pdf_start
        )

        print(
            "📄 PDF retrieval time:",
            round(
                pdf_time,
                2
            ),
            "seconds"
        )

        top_pdf_results = pdf_results[:3]

        pdf_context = build_pdf_context(
            top_pdf_results
        )

        if not pdf_context:

            pdf_context = (
                "No relevant ESS PDF "
                "information was found."
            )

        # ----------------------------------------------------
        # Prompt
        # ----------------------------------------------------

        prompt = build_hybrid_prompt(

            message,

            csv_answer,

            pdf_context

        )

        # ----------------------------------------------------
        # Ollama
        # ----------------------------------------------------

        answer = ask_ollama(
            prompt
        )

        sources = build_pdf_sources(
            top_pdf_results
        )

        sources.append({

            "document":
                "ESS CSV Dataset",

            "category":
                "CSV"

        })

        return {

            "answer":
                answer,

            "sources":
                sources,

            "type":
                "hybrid"

        }

    # ========================================================
    # 5. CSV ONLY
    # ========================================================

    if (
        source["csv_dataset"]
        or source["csv_operation"]
        or source["csv_name"]
    ):

        print(
            "\n📊 CSV QUESTION DETECTED"
        )

        csv_start = time.time()

        csv_result = (
            csv_ai_service.answer(
                message
            )
        )

        csv_time = (
            time.time()
            - csv_start
        )

        print(
            "📊 CSV processing time:",
            round(
                csv_time,
                2
            ),
            "seconds"
        )

        return {

            "answer":
                csv_result.get(
                    "answer",
                    "No relevant CSV result was found."
                ),

            "sources": [

                {

                    "document":
                        "ESS CSV Dataset",

                    "category":
                        "CSV"

                }

            ],

            "type":
                "csv"

        }

    # ========================================================
    # 6. NORMAL ESS PDF / RAG
    # ========================================================

    print(
        "\n📚 SEARCHING ESS PDF DOCUMENTS"
    )

    pdf_start = time.time()

    results = retriever.search(
        message
    )

    pdf_time = (
        time.time()
        - pdf_start
    )

    print(
        "📄 PDF retrieval time:",
        round(
            pdf_time,
            2
        ),
        "seconds"
    )

    if not results:

        print(
            "❌ No PDF results found"
        )

        return {

            "answer":
                no_pdf_information_response(
                    uploaded=False
                ),

            "sources": [],

            "type":
                "pdf"

        }

    print(
        "✅ Relevant PDF found"
    )

    # Keep strongest chunks
    top_results = results[:3]

    context = build_pdf_context(
        top_results
    )

    print(
        "\n========== FINAL CONTEXT SIZE =========="
    )

    total_chars = 0

    for item in top_results:

        chars = len(
            item.get(
                "text",
                ""
            )
        )

        total_chars += chars

        print(

            item.get(
                "document"
            ),

            "page:",

            item.get(
                "page"
            ),

            "chars:",

            chars

        )

    print(
        "Total characters sent:",
        total_chars
    )

    print(
        "========================================"
    )

    print(
        "Chunks sent:",
        len(top_results)
    )

    print(
        "Context length:",
        len(context)
    )

    if not context.strip():

        print(
            "❌ Empty PDF context"
        )

        return {

            "answer":
                no_pdf_information_response(
                    uploaded=False
                ),

            "sources": [],

            "type":
                "pdf"

        }

    prompt = build_pdf_prompt(

        message,

        context,

        uploaded=False

    )

    print(
        "Prompt length:",
        len(prompt)
    )

    answer = ask_ollama(
        prompt
    )

    unique_sources = build_pdf_sources(
        top_results
    )

    total_time = (
        time.time()
        - total_start
    )

    print(
        "⏱️ Total PDF processing time:",
        round(
            total_time,
            2
        ),
        "seconds"
    )

    return {

        "answer":
            answer,

        "sources":
            unique_sources,

        "type":
            "pdf"

    }


# ============================================================
# CACHED AI ENTRY POINT
# ============================================================

def ask_ai(
    message: str,
    file_id: str | None = None
):

    start_time = time.time()

    print(
        "\n" + "=" * 70
    )

    print(
        "🤖 ASK AI"
    )

    print(
        "Message:",
        message
    )

    print(
        "File ID:",
        file_id
    )

    print(
        "=" * 70
    )

    # ========================================================
    # GREETING
    # ========================================================

    question = normalize_question(
        message
    )

    if is_greeting(question):

        print(
            "👋 Greeting detected."
        )

        print(
            "🚫 RAG search skipped."
        )

        print(
            "🚫 CSV search skipped."
        )

        return greeting_response()

    # ========================================================
    # CACHE
    # ========================================================

    cached_result = get_cached_response(

        message,

        file_id=file_id

    )

    if cached_result is not None:

        print(
            "⚡ Cached response time:",
            round(
                time.time()
                - start_time,
                4
            ),
            "seconds"
        )

        return cached_result

    print(
        "⚡ CACHE MISS"
    )

    # ========================================================
    # GENERATE RESPONSE
    # ========================================================

    result = _ask_ai_uncached(

        message,

        file_id=file_id

    )

    # ========================================================
    # SAVE RESPONSE
    # ========================================================

    save_cached_response(

        message,

        result,

        file_id=file_id

    )

    return result
