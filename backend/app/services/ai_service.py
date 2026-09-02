# ============================================================
# ESS AI SERVICE
# ============================================================

import os
import re
import time
import requests
from typing import Optional

from dotenv import load_dotenv

from app.rag.retriever import Retriever
from app.services.csv_ai_service import csv_ai_service


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


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
# CACHE
# ============================================================

AI_CACHE = {}

CACHE_TTL = 3600
CACHE_MAX_SIZE = 100


def normalize_question(question: str) -> str:
    """
    Normalize a question for cache lookup.
    """

    if not question:
        return ""

    question = question.lower().strip()

    question = re.sub(r"\s+", " ", question)

    question = question.strip(" ?!.,:")

    return question


def make_cache_key(
    question: str,
    file_id: Optional[str] = None
) -> str:

    normalized = normalize_question(question)

    return f"{file_id or 'global'}::{normalized}"


def get_cached_answer(
    question: str,
    file_id: Optional[str] = None
):

    key = make_cache_key(question, file_id)

    item = AI_CACHE.get(key)

    if not item:
        return None

    timestamp, value = item

    if time.time() - timestamp > CACHE_TTL:

        try:
            del AI_CACHE[key]
        except KeyError:
            pass

        return None

    return value


def save_cached_answer(
    question: str,
    answer,
    file_id: Optional[str] = None
):

    if len(AI_CACHE) >= CACHE_MAX_SIZE:

        oldest_key = min(
            AI_CACHE,
            key=lambda k: AI_CACHE[k][0]
        )

        try:
            del AI_CACHE[oldest_key]
        except KeyError:
            pass

    key = make_cache_key(question, file_id)

    AI_CACHE[key] = (
        time.time(),
        answer
    )


# ============================================================
# GREETING
# ============================================================

def is_greeting(question: str) -> bool:

    if not question:
        return False

    text = question.lower().strip()

    greetings = {
        "hi",
        "hello",
        "hey",
        "hiya",
        "howdy",
        "good morning",
        "good afternoon",
        "good evening",
        "morning",
        "afternoon",
        "evening",
        "selam",
        "salam",
        "እንደምን አለህ",
        "እንደምን አለሽ",
        "ሰላም",
    }

    if text in greetings:
        return True

    return False


def greeting_response() -> str:

    return (
        "Welcome to the Ethiopia Statistical Service (ESS) "
        "AI Assistant. How can I help you today?"
    )


# ============================================================
# QUESTION INTENT
# ============================================================

def detect_question_intent(question: str) -> str:

    if not question:
        return "general"

    text = question.lower()

    # --------------------------------------------------------
    # Definition / comparison questions
    # --------------------------------------------------------

    definition_words = [
        "definition",
        "define",
        "what is",
        "what are",
        "meaning of",
        "means",
        "difference between",
        "difference",
        "distinguish",
        "distinction",
        "compare",
        "comparison",
    ]

    if any(word in text for word in definition_words):

        return "definition"

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary_words = [
        "summarize",
        "summary",
        "main findings",
        "key findings",
        "overview",
        "highlights",
        "main points",
    ]

    if any(word in text for word in summary_words):

        return "summary"

    # --------------------------------------------------------
    # Rate / percentage
    # --------------------------------------------------------

    rate_words = [
        "rate",
        "percentage",
        "percent",
        "%",
        "proportion",
        "share",
    ]

    if any(word in text for word in rate_words):

        return "value"

    # --------------------------------------------------------
    # Count
    # --------------------------------------------------------

    count_words = [
        "how many",
        "number of",
        "count",
        "total number",
    ]

    if any(word in text for word in count_words):

        return "count"

    # --------------------------------------------------------
    # Trend
    # --------------------------------------------------------

    trend_words = [
        "trend",
        "increase",
        "decrease",
        "increased",
        "decreased",
        "change",
        "changed",
        "growth",
        "decline",
        "over time",
    ]

    if any(word in text for word in trend_words):

        return "trend"

    return "general"


# ============================================================
# SOURCE DETECTION
# ============================================================

def detect_source(question: str) -> str:

    if not question:
        return "pdf"

    text = question.lower()

    csv_keywords = [
        "csv",
        "dataset",
        "data set",
        "column",
        "row",
        "average",
        "mean",
        "median",
        "maximum",
        "minimum",
        "max",
        "min",
        "standard deviation",
        "variance",
        "quartile",
        "percentile",
        "correlation",
        "unique values",
    ]

    if any(keyword in text for keyword in csv_keywords):

        return "csv"

    pdf_keywords = [
        "report",
        "survey",
        "publication",
        "document",
        "pdf",
        "according to",
        "according to the report",
        "statistical report",
        "key findings",
        "inflation",
        "employment",
        "unemployment",
        "employed",
        "unemployed",
        "labour",
        "labor",
        "population",
        "census",
        "price",
        "consumer price",
    ]

    if any(keyword in text for keyword in pdf_keywords):

        return "pdf"

    return "pdf"


# ============================================================
# RETRIEVAL QUERY
# ============================================================

def build_retrieval_query(question: str) -> str:
    """
    Improve semantic retrieval without changing the user's
    actual question.

    This query is ONLY used for searching Chroma.

    The model still answers using the retrieved ESS evidence.
    """

    if not question:
        return question

    text = question.lower()

    additions = []

    # --------------------------------------------------------
    # Employment definitions
    # --------------------------------------------------------

    if (
        "employed" in text
        or "unemployed" in text
        or "employment" in text
        or "unemployment" in text
    ):

        additions.extend([
            "employment status",
            "employed persons definition",
            "unemployed persons definition",
            "employed population",
            "unemployed population",
            "labour force",
            "labor force",
            "ESS definition",
        ])

    # --------------------------------------------------------
    # Explicit comparison questions
    # --------------------------------------------------------

    if (
        "difference between" in text
        or "compare" in text
        or "comparison" in text
        or "distinguish" in text
    ):

        additions.extend([
            "definition of first concept",
            "definition of second concept",
            "statistical definition",
            "employment status classification",
        ])

    # --------------------------------------------------------
    # Labour force
    # --------------------------------------------------------

    if (
        "labour force" in text
        or "labor force" in text
    ):

        additions.extend([
            "labour force definition",
            "labor force definition",
            "employment status",
            "unemployment definition",
        ])

    # --------------------------------------------------------
    # Inflation
    # --------------------------------------------------------

    if (
        "inflation" in text
        or "inflation rate" in text
    ):

        additions.extend([
            "inflation rate",
            "consumer price index",
            "CPI",
        ])

    # --------------------------------------------------------
    # Don't make the query unnecessarily huge
    # --------------------------------------------------------

    if not additions:

        return question

    return question + " " + " ".join(additions)


# ============================================================
# REMOVE DUPLICATE RESULTS
# ============================================================

def remove_duplicate_results(results):
    """
    Remove identical or nearly identical PDF chunks.

    This is important because the same ESS PDF may have been
    uploaded/indexed multiple times under different file_ids.
    """

    if not results:
        return []

    unique_results = []

    seen_text = set()

    for result in results:

        text = result.get(
            "text",
            result.get(
                "content",
                ""
            )
        )

        if not text:
            continue

        # Normalize whitespace
        normalized = " ".join(
            text.strip().split()
        )

        if not normalized:
            continue

        # Skip exact duplicate chunks
        if normalized in seen_text:
            continue

        seen_text.add(normalized)

        unique_results.append(result)

    return unique_results


# ============================================================
# LIMIT RESULT TEXT
# ============================================================

def limit_result_text(
    text: str,
    max_chars: int = 1800
) -> str:
    """
    Prevent very large PDF chunks from being sent to Ollama.
    """

    if not text:
        return ""

    text = text.strip()

    if len(text) <= max_chars:
        return text

    return text[:max_chars].rstrip() + "..."


# ============================================================
# PDF CONTEXT
# ============================================================

def build_pdf_context(results) -> str:

    if not results:
        return ""

    context_parts = []

    for index, result in enumerate(
        results,
        start=1
    ):

        metadata = result.get(
            "metadata",
            {}
        )

        document = metadata.get(
            "document",
            metadata.get(
                "filename",
                "Unknown document"
            )
        )

        page = metadata.get(
            "page",
            metadata.get(
                "page_number",
                "Unknown"
            )
        )

        category = metadata.get(
            "category",
            "ESS document"
        )

        text = result.get(
            "text",
            result.get(
                "content",
                ""
            )
        )

        if not text:
            continue

        # Limit chunk size
        text = limit_result_text(
            text,
            max_chars=1800
        )

        context_parts.append(
            f"""
--- EVIDENCE {index} ---
Document: {document}
Category: {category}
Page: {page}

{text}
""".strip()
        )

    return "\n\n".join(
        context_parts
    )


# ============================================================
# PDF SOURCES
# ============================================================

def build_pdf_sources(results):

    sources = []

    if not results:
        return sources

    seen = set()

    for result in results:

        metadata = result.get(
            "metadata",
            {}
        )

        document = metadata.get(
            "document",
            metadata.get(
                "filename",
                "Unknown document"
            )
        )

        page = metadata.get(
            "page",
            metadata.get(
                "page_number",
                None
            )
        )

        key = (
            str(document),
            str(page)
        )

        if key in seen:
            continue

        seen.add(key)

        sources.append({
            "document": document,
            "page": page,
            "category": metadata.get(
                "category",
                None
            )
        })

    return sources


# ============================================================
# NO PDF INFORMATION
# ============================================================

def no_pdf_information_response():

    return (
        "The requested information was not found in the "
        "provided ESS documents."
    )


# ============================================================
# PDF PROMPT
# ============================================================

def build_pdf_prompt(
    question: str,
    context: str
) -> str:

    intent = detect_question_intent(
        question
    )

    # ========================================================
    # DEFINITION / COMPARISON
    # ========================================================

    if intent == "definition":

        task = """
This is a DEFINITION or COMPARISON question.

Use the ESS evidence to answer the question.

If the user asks for the difference between two concepts:

1. Identify the ESS definition of the FIRST concept.
2. Identify the ESS definition of the SECOND concept.
3. Explain BOTH concepts.
4. Clearly explain the difference between them.
5. Preserve important ESS conditions, thresholds,
   classifications, age requirements, time periods,
   or other criteria.
6. Do not replace an ESS statistical definition with
   a generic textbook definition.
7. Do not use outside knowledge.
8. Do not invent missing information.
9. If only one concept is supported by the evidence,
   clearly say that the available evidence only supports
   that concept instead of inventing the other definition.

For employment questions, specifically look for:
- employed persons
- unemployed persons
- employment status
- labour force
- statistical definitions
"""
    
    # ========================================================
    # SUMMARY
    # ========================================================

    elif intent == "summary":

        task = """
This is a SUMMARY question.

Use ONLY the supplied ESS evidence.

Provide the main findings relevant to the question.

Include important indicators, trends, classifications,
and key changes when they are present.

Do not focus on one isolated number when the user asks
for a summary.
"""

    # ========================================================
    # EXACT VALUE
    # ========================================================

    elif intent == "value":

        task = """
This question asks for a statistical value, rate,
percentage, proportion, or similar indicator.

Use ONLY the supplied ESS evidence.

Return the exact value appearing in the evidence.

Be careful about:

- year
- month
- survey round
- geographic area
- population group
- numerator
- denominator
- unit
- percentage versus percentage points

Do not calculate or guess a value unless the evidence
clearly provides the required information.
"""

    # ========================================================
    # COUNT
    # ========================================================

    elif intent == "count":

        task = """
This question asks for a count or number.

Use ONLY the supplied ESS evidence.

Return the exact number from the relevant evidence.

Do not substitute a percentage for a count.

Pay attention to the population, year, survey round,
geographic area, and unit.
"""

    # ========================================================
    # TREND
    # ========================================================

    elif intent == "trend":

        task = """
This is a trend or change question.

Use ONLY the supplied ESS evidence.

Explain the direction and magnitude of change when the
evidence provides it.

Do not infer a trend that is not supported by the evidence.
"""

    # ========================================================
    # GENERAL
    # ========================================================

    else:

        task = """
Answer the question using ONLY the ESS evidence below.

Do not use outside knowledge.

If the evidence does not contain enough information to
answer the question, say:

"The requested information was not found in the provided
ESS documents."

Do not guess.
"""

    # ========================================================
    # FINAL PROMPT
    # ========================================================

    prompt = f"""
You are the Ethiopia Statistical Service (ESS) AI Assistant.

You are answering a question using retrieved ESS statistical
documents.

IMPORTANT:
This is an evidence-based question answering task.

The retrieved evidence is the ONLY authoritative source
for your answer.

Do NOT answer from your general knowledge or training data.

{task}

Additional rules:

- Use ESS terminology.
- Do not invent facts.
- Do not hallucinate.
- Do not mix information from unrelated years or surveys.
- Do not assume two statistics are comparable unless the
  evidence supports the comparison.
- If the evidence contains a definition, follow that definition.
- If the evidence contains conditions or criteria, preserve them.
- If the evidence contains an exact number, preserve the number.
- Keep the answer concise but complete.
- Mention the document/page when useful.
- Never claim that something appears in the evidence when it
  does not.

============================================================
USER QUESTION
============================================================

{question}

============================================================
ESS EVIDENCE
============================================================

{context}

============================================================
ANSWER
============================================================

Answer directly from the ESS evidence.
""".strip()

    return prompt


# ============================================================
# HYBRID PROMPT
# ============================================================

def build_hybrid_prompt(
    question: str,
    pdf_context: str,
    csv_context: str = ""
) -> str:

    return f"""
You are the Ethiopia Statistical Service (ESS) AI Assistant.

Answer the user's question using the supplied ESS information.

IMPORTANT:

- Use the supplied evidence.
- Do not invent information.
- Do not use generic definitions when an ESS definition is
  available.
- Do not mix unrelated datasets or reports.
- Preserve exact statistical values.
- If the information is not available, say so.

USER QUESTION:

{question}

============================================================
PDF EVIDENCE
============================================================

{pdf_context}

============================================================
CSV / DATA EVIDENCE
============================================================

{csv_context}

============================================================
ANSWER
============================================================
""".strip()


# ============================================================
# OLLAMA OPTIONS
# ============================================================

OLLAMA_OPTIONS = {
    "temperature": 0.0,
    "num_predict": 300,

    # Reduced from 4096 to reduce prompt processing time
    "num_ctx": 2048,

    "top_k": 10,
    "top_p": 0.5,

    # Keep the model loaded
    "keep_alive": "30m",
}


# ============================================================
# OLLAMA NON-STREAMING
# ============================================================

def ask_ollama(prompt: str) -> str:

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": OLLAMA_OPTIONS,
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=180
        )

        response.raise_for_status()

        data = response.json()

        answer = data.get(
            "response",
            ""
        )

        return answer.strip()

    except Exception as exc:

        print(
            f"Ollama request failed: {exc}"
        )

        return (
            "I was unable to generate an answer at this time."
        )


# ============================================================
# OLLAMA STREAMING
# ============================================================

def stream_ollama(prompt: str):

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": True,
        "options": OLLAMA_OPTIONS,
    }

    print(
        "\nStarting Ollama stream..."
    )

    print(
        f"Streaming prompt length: {len(prompt)} characters"
    )

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            stream=True,
            timeout=180
        )

        response.raise_for_status()

        for line in response.iter_lines():

            if not line:
                continue

            yield line

    except Exception as exc:

        print(
            f"Ollama streaming failed: {exc}"
        )

        yield (
            '{"response":"Unable to generate an answer.","done":true}'
            .encode("utf-8")
        )


# ============================================================
# INTERNAL AI
# ============================================================

def _ask_ai_uncached(
    question: str,
    file_id: Optional[str] = None
):

    question = question.strip()

    # ========================================================
    # GREETING
    # ========================================================

    if is_greeting(question):

        print(
            "Greeting detected."
        )

        return {
            "response": greeting_response(),
            "sources": [],
            "type": "llm",
        }

    # ========================================================
    # SOURCE
    # ========================================================

    source = detect_source(
        question
    )

    print(
        f"Detected source: {source}"
    )

    # ========================================================
    # CSV
    # ========================================================

    if source == "csv":

        print(
            "CSV question detected."
        )

        try:

            csv_answer = csv_ai_service.answer(
                question
            )

            if isinstance(
                csv_answer,
                dict
            ):

                return csv_answer

            return {
                "response": str(
                    csv_answer
                ),
                "sources": [],
                "type": "csv",
            }

        except Exception as exc:

            print(
                f"CSV service failed: {exc}"
            )

            return {
                "response": (
                    "I could not process the requested "
                    "ESS dataset information."
                ),
                "sources": [],
                "type": "csv",
            }

    # ========================================================
    # PDF
    # ========================================================

    print(
        "\nESS-WIDE SEARCH"
    )

    retrieval_query = build_retrieval_query(
        question
    )

    print(
        f"Retrieval query: {retrieval_query}"
    )

    # ========================================================
    # RETRIEVE
    # ========================================================

    try:

        if file_id:

            print(
                f"Searching uploaded file: {file_id}"
            )

            results = retriever.search(
                retrieval_query,
                file_id=file_id
            )

        else:

            results = retriever.search(
                retrieval_query
            )

    except TypeError:

        # Backward compatibility
        results = retriever.search(
            retrieval_query
        )

    except Exception as exc:

        print(
            f"Retriever failed: {exc}"
        )

        return {
            "response": no_pdf_information_response(),
            "sources": [],
            "type": "pdf",
        }

    # ========================================================
    # NO RESULTS
    # ========================================================

    if not results:

        print(
            "No PDF results found."
        )

        return {
            "response": no_pdf_information_response(),
            "sources": [],
            "type": "pdf",
        }

    print(
        f"Raw retrieval results: {len(results)}"
    )

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    unique_results = remove_duplicate_results(
        results
    )

    print(
        f"Unique results after deduplication: "
        f"{len(unique_results)}"
    )

    if not unique_results:

        print(
            "No unique PDF results found."
        )

        return {
            "response": no_pdf_information_response(),
            "sources": [],
            "type": "pdf",
        }

    # ========================================================
    # KEEP BEST RESULTS
    # ========================================================

    # We previously sent up to 6 chunks.
    #
    # That caused large prompts and slow prompt evaluation.
    #
    # Now we send only the best 3 UNIQUE chunks.
    #
    # This is enough for most ESS questions while preserving
    # multiple definitions for comparison questions.

    top_results = unique_results[:3]

    print(
        f"Results sent to Ollama: {len(top_results)}"
    )

    # ========================================================
    # PRINT RETRIEVED EVIDENCE
    # ========================================================

    for index, result in enumerate(
        top_results,
        start=1
    ):

        metadata = result.get(
            "metadata",
            {}
        )

        page = metadata.get(
            "page",
            metadata.get(
                "page_number",
                "Unknown"
            )
        )

        text = result.get(
            "text",
            result.get(
                "content",
                ""
            )
        )

        print(
            f"\n--- RESULT {index} ---"
        )

        print(
            f"PAGE: {page}"
        )

        print(
            f"TEXT: {text[:500]}"
        )

    # ========================================================
    # CONTEXT
    # ========================================================

    context = build_pdf_context(
        top_results
    )

    print(
        f"\nPrompt context length: {len(context)} characters"
    )

    if not context.strip():

        return {
            "response": no_pdf_information_response(),
            "sources": [],
            "type": "pdf",
        }

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = build_pdf_prompt(
        question,
        context
    )

    print(
        f"Prompt length: {len(prompt)} characters"
    )

    # ========================================================
    # ASK OLLAMA
    # ========================================================

    start_time = time.time()

    answer = ask_ollama(
        prompt
    )

    ollama_time = time.time() - start_time

    print(
        f"Ollama generation time: "
        f"{ollama_time:.2f}s"
    )

    # ========================================================
    # SAFETY FALLBACK
    # ========================================================

    if not answer.strip():

        answer = no_pdf_information_response()

    # ========================================================
    # SOURCES
    # ========================================================

    sources = build_pdf_sources(
        top_results
    )

    return {
        "response": answer,
        "sources": sources,
        "type": "pdf",
    }


# ============================================================
# PUBLIC AI FUNCTION
# ============================================================

def ask_ai(
    question: str,
    file_id: Optional[str] = None
):

    if not question:

        return {
            "response": (
                "Please enter a question."
            ),
            "sources": [],
            "type": "llm",
        }

    question = question.strip()

    # ========================================================
    # GREETING
    # ========================================================

    if is_greeting(question):

        return {
            "response": greeting_response(),
            "sources": [],
            "type": "llm",
        }

    # ========================================================
    # CACHE
    # ========================================================

    cached = get_cached_answer(
        question,
        file_id
    )

    if cached is not None:

        print(
            "AI cache hit."
        )

        return cached

    # ========================================================
    # AI
    # ========================================================

    result = _ask_ai_uncached(
        question,
        file_id
    )

    # ========================================================
    # CACHE
    # ========================================================

    save_cached_answer(
        question,
        result,
        file_id
    )

    return result