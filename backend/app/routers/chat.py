from datetime import datetime, timezone
import json
import re
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.schemas.chat import ChatRequest
from app.dependencies.auth import get_current_user
from app.models.user import User

from app.services.ai_service import (
    ask_ai,
    stream_ollama,
    is_greeting,
    retriever,
)

from app.database.connection import get_db
from app.services.chat_history_service import chat_history_service


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


# =========================================================
# RESULT CLEANING / SELECTION
# =========================================================

def normalize_text(text: str) -> str:
    """
    Normalize whitespace so duplicate PDF chunks can be detected.
    """

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def remove_duplicate_results(results: list) -> list:
    """
    Remove duplicate chunks based on normalized text.
    """

    unique = []
    seen = set()

    for item in results:

        text = normalize_text(
            item.get("text", "")
        )

        if not text:
            continue

        key = text.lower()

        if key in seen:
            continue

        seen.add(key)
        unique.append(item)

    return unique


def is_employment_comparison(question: str) -> bool:
    """
    Detect questions comparing employed and unemployed persons.
    """

    q = question.lower()

    return (
        "employed" in q
        and "unemployed" in q
        and (
            "difference" in q
            or "compare" in q
            or "comparison" in q
            or "between" in q
            or "versus" in q
            or " vs " in q
        )
    )


def select_best_results(
    question: str,
    results: list,
    max_results: int = 3
) -> list:
    """
    Select a small but useful set of PDF chunks.

    For employment comparison questions, prioritize chunks
    containing evidence about both employed and unemployed
    persons.
    """

    if not results:
        return []

    # -----------------------------------------------------
    # Remove exact duplicate chunks
    # -----------------------------------------------------

    unique_results = remove_duplicate_results(
        results
    )

    print(
        "🧹 Results after duplicate removal:",
        len(unique_results)
    )

    # -----------------------------------------------------
    # Employment comparison
    # -----------------------------------------------------

    if is_employment_comparison(question):

        both_terms = []
        employed_only = []
        unemployed_only = []

        for item in unique_results:

            text = normalize_text(
                item.get("text", "")
            )

            lower_text = text.lower()

            has_employed = (
                "employed" in lower_text
                or "employment" in lower_text
            )

            has_unemployed = (
                "unemployed" in lower_text
                or "unemployment" in lower_text
            )

            if has_employed and has_unemployed:

                both_terms.append(item)

            elif has_employed:

                employed_only.append(item)

            elif has_unemployed:

                unemployed_only.append(item)

        selected = []

        # -------------------------------------------------
        # Best case:
        # A chunk contains BOTH concepts.
        # -------------------------------------------------

        for item in both_terms:

            if item not in selected:
                selected.append(item)

            if len(selected) >= max_results:
                break

        # -------------------------------------------------
        # Make sure employed evidence exists.
        # -------------------------------------------------

        for item in employed_only:

            if len(selected) >= max_results:
                break

            if item not in selected:
                selected.append(item)

        # -------------------------------------------------
        # Make sure unemployed evidence exists.
        # -------------------------------------------------

        for item in unemployed_only:

            if len(selected) >= max_results:
                break

            if item not in selected:
                selected.append(item)

        # -------------------------------------------------
        # Fill remaining slots using normal ranking.
        # -------------------------------------------------

        for item in unique_results:

            if len(selected) >= max_results:
                break

            if item not in selected:
                selected.append(item)

        print(
            "🎯 Employment comparison selection:",
            len(selected)
        )

        return selected[:max_results]

    # -----------------------------------------------------
    # Normal questions
    # -----------------------------------------------------

    return unique_results[:max_results]


# =========================================================
# LIMIT CHUNK SIZE
# =========================================================

def limit_result_text(
    text: str,
    max_chars: int = 1800
) -> str:
    """
    Prevent a single PDF chunk from making the prompt huge.
    """

    if not text:
        return ""

    text = text.strip()

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "..."


# =========================================================
# BUILD PDF PROMPT
# =========================================================

def build_pdf_prompt(
    question: str,
    results: list
) -> str:
    """
    Build a compact ESS-only prompt.

    Only the selected high-quality chunks should be passed here.
    """

    context_parts = []

    for index, item in enumerate(
        results,
        start=1
    ):

        metadata = item.get(
            "metadata",
            {}
        )

        filename = (
            metadata.get("filename")
            or metadata.get("file_name")
            or metadata.get("source")
            or "ESS PDF"
        )

        page = metadata.get(
            "page",
            "unknown"
        )

        text = limit_result_text(
            item.get("text", ""),
            max_chars=1800
        )

        if not text:
            continue

        context_parts.append(
            f"[Source {index}]\n"
            f"Document: {filename}\n"
            f"Page: {page}\n"
            f"Text:\n{text}"
        )

    context = "\n\n------------------------\n\n".join(
        context_parts
    )

    # -----------------------------------------------------
    # Special instructions for comparison questions
    # -----------------------------------------------------

    comparison_instruction = ""

    if is_employment_comparison(question):

        comparison_instruction = """
For this question specifically:

- Define employed persons using the ESS context.
- Define unemployed persons using the ESS context.
- Clearly explain the difference between them.
- If the context provides age, work-hour, availability, job-search,
  or labour-force criteria, include them when relevant.
- Do not answer with only the definition of unemployed persons.
- Do not describe employed persons as seeking employment unless
  the ESS context explicitly says so.
- Keep the two definitions clearly separated.
"""

    prompt = f"""
You are an Ethiopian Statistical Service (ESS) AI assistant.

Answer ONLY using the provided ESS PDF context.

Rules:

- Do not use outside knowledge.
- Do not guess.
- Give a direct answer to the user's question.
- If the question asks for a definition, give the relevant definition
  from the ESS documents.
- If the question asks for a comparison or difference, explain BOTH
  concepts before explaining their difference.
- If the question asks for a specific rate or value, return the exact
  value found in the context.
- If the question asks for a summary, provide the main findings,
  important indicators, trends, and key changes.
- If the information is not present in the context, say:
  "The information was not found in the provided ESS documents."
- Keep the answer concise and clear.
- Do not combine or confuse definitions from different concepts.

{comparison_instruction}

ESS PDF CONTEXT:

{context}

USER QUESTION:

{question}

FINAL ANSWER:
"""

    return prompt.strip()


# =========================================================
# EXTRACT SOURCES
# =========================================================

def extract_sources(
    results: list
) -> list:

    sources = []

    for item in results:

        metadata = item.get(
            "metadata",
            {}
        )

        source = (
            metadata.get("filename")
            or metadata.get("file_name")
            or metadata.get("source")
            or "ESS PDF"
        )

        if source not in sources:
            sources.append(source)

    return sources


# =========================================================
# SAVE CHAT HISTORY
# =========================================================

def save_history(
    db: Session,
    user_id: int,
    message: str,
    response: str,
    chat_type: str = "pdf"
):

    try:

        print("\n" + "-" * 60)
        print("💾 SAVING CHAT HISTORY")
        print("-" * 60)

        print("User ID:", user_id)
        print("Message:", message)
        print("Response length:", len(response))
        print("Chat type:", chat_type)

        saved = chat_history_service.save_chat(
            db=db,
            user_id=user_id,
            message=message,
            response=response,
            chat_type=chat_type
        )

        try:

            db.commit()

        except Exception:

            db.rollback()
            raise

        print("✅ CHAT HISTORY SAVED")
        print("-" * 60)

        return saved

    except Exception as e:

        print("\n" + "=" * 60)
        print("❌ CHAT HISTORY SAVE FAILED")
        print("=" * 60)

        print("User ID:", user_id)
        print("Error:", repr(e))

        print("=" * 60)

        try:
            db.rollback()
        except Exception:
            pass

        return None


# =========================================================
# NORMALIZE OLLAMA STREAM
# =========================================================

def normalize_ollama_chunk(chunk):

    if chunk is None:
        return None

    # -----------------------------------------------------
    # Already dictionary
    # -----------------------------------------------------

    if isinstance(chunk, dict):

        response_text = chunk.get(
            "response",
            ""
        )

        done = chunk.get(
            "done",
            False
        )

        return {
            "response": response_text,
            "done": done
        }

    # -----------------------------------------------------
    # Convert bytes/string
    # -----------------------------------------------------

    if isinstance(chunk, bytes):

        try:

            chunk = chunk.decode(
                "utf-8"
            )

        except Exception:

            chunk = str(chunk)

    elif not isinstance(chunk, str):

        chunk = str(chunk)

    chunk = chunk.strip()

    if not chunk:
        return None

    # -----------------------------------------------------
    # JSON
    # -----------------------------------------------------

    try:

        parsed = json.loads(
            chunk
        )

        if isinstance(parsed, dict):

            response_text = parsed.get(
                "response",
                ""
            )

            done = parsed.get(
                "done",
                False
            )

            return {
                "response": response_text,
                "done": done
            }

    except json.JSONDecodeError:

        pass

    # -----------------------------------------------------
    # Plain text fallback
    # -----------------------------------------------------

    return {
        "response": chunk,
        "done": False
    }


# =========================================================
# STREAM AI RESPONSE
# =========================================================

def stream_clean_response(
    prompt: str
):

    """
    Reads raw Ollama streaming output and returns
    clean NDJSON-compatible chunks.
    """

    for raw_chunk in stream_ollama(
        prompt
    ):

        parsed = normalize_ollama_chunk(
            raw_chunk
        )

        if parsed is None:
            continue

        if parsed.get("done") is True:
            continue

        response_text = parsed.get(
            "response",
            ""
        )

        if response_text:

            yield json.dumps({
                "response": response_text,
                "done": False
            })


# =========================================================
# PUBLIC CHAT
# =========================================================

@router.post("/public")
def public_chat(
    request: ChatRequest
):

    start_time = time.time()

    print("\n" + "=" * 70)
    print("👤 PUBLIC CHAT REQUEST")
    print("=" * 70)

    print(
        "Question:",
        request.message
    )

    print(
        "File ID:",
        request.file_id
    )

    result = ask_ai(
        request.message,
        file_id=request.file_id
    )

    end_time = time.time()

    print(
        "⏱️ Public AI processing time:",
        round(
            end_time - start_time,
            2
        ),
        "seconds"
    )

    return {
        "user": "Guest",
        "message": request.message,
        "response": result["answer"],
        "sources": result["sources"],
        "type": result.get(
            "type",
            "unknown"
        ),
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat()
    }


# =========================================================
# PUBLIC STREAMING CHAT
# =========================================================

@router.post("/public/stream")
def public_chat_stream(
    request: ChatRequest
):

    start_time = time.time()

    print("\n" + "=" * 70)
    print("🌊 PUBLIC STREAMING CHAT REQUEST")
    print("=" * 70)

    print(
        "Question:",
        request.message
    )

    print(
        "File ID:",
        request.file_id
    )

    # =====================================================
    # GREETING
    # =====================================================

    if is_greeting(
        request.message
    ):

        print(
            "👋 Greeting detected."
        )

        print(
            "🚫 RAG search skipped."
        )

        def greeting_response():

            yield json.dumps({
                "response": (
                    "Welcome to the Ethiopia Statistical Service "
                    "(ESS) AI Assistant. How can I help you today?"
                ),
                "sources": [],
                "type": "llm",
                "done": True
            }) + "\n"

        print(
            "⏱️ Greeting response time:",
            round(
                time.time() - start_time,
                4
            ),
            "seconds"
        )

        return StreamingResponse(
            greeting_response(),
            media_type="application/x-ndjson"
        )

    # =====================================================
    # IMPORTANT:
    # DO NOT CREATE Retriever() HERE
    #
    # We use the singleton retriever imported from
    # app.services.ai_service.
    # =====================================================

    print(
        "♻️ Using shared ESS Retriever instance"
    )

    # =====================================================
    # PDF RETRIEVAL
    # =====================================================

    pdf_start = time.time()

    raw_results = retriever.search(
        request.message,
        file_id=request.file_id
    )

    pdf_time = time.time() - pdf_start

    print(
        "📄 Streaming PDF retrieval time:",
        round(
            pdf_time,
            2
        ),
        "seconds"
    )

    print(
        "Raw retrieval results:",
        len(raw_results)
    )

    # =====================================================
    # NO RESULTS
    # =====================================================

    if not raw_results:

        print(
            "❌ No PDF results found"
        )

        def no_result():

            yield json.dumps({
                "response": (
                    "The information was not found "
                    "in the provided ESS documents."
                ),
                "sources": [],
                "type": "pdf",
                "done": True
            }) + "\n"

        return StreamingResponse(
            no_result(),
            media_type="application/x-ndjson"
        )

    # =====================================================
    # SELECT BEST RESULTS
    # =====================================================

    question = request.message.strip()

    results = select_best_results(
        question,
        raw_results,
        max_results=3
    )

    print(
        "🎯 Final chunks selected:",
        len(results)
    )

    # =====================================================
    # SHOW SELECTED EVIDENCE
    # =====================================================

    print("\n" + "=" * 70)
    print("📚 SELECTED PDF EVIDENCE")
    print("=" * 70)

    for index, item in enumerate(
        results,
        start=1
    ):

        metadata = item.get(
            "metadata",
            {}
        )

        filename = (
            metadata.get("filename")
            or metadata.get("file_name")
            or metadata.get("source")
            or "ESS PDF"
        )

        page = metadata.get(
            "page",
            "unknown"
        )

        text = normalize_text(
            item.get("text", "")
        )

        print(
            f"\nChunk #{index}"
        )

        print(
            "Document:",
            filename
        )

        print(
            "Page:",
            page
        )

        print(
            "Text:",
            text[:500]
        )

    print("=" * 70)

    # =====================================================
    # BUILD PROMPT
    # =====================================================

    prompt = build_pdf_prompt(
        question,
        results
    )

    print(
        "Chunks sent:",
        len(results)
    )

    print(
        "Prompt length:",
        len(prompt)
    )

    # =====================================================
    # SOURCES
    # =====================================================

    sources = extract_sources(
        results
    )

    # =====================================================
    # GENERATOR
    # =====================================================

    def generate():

        try:

            print(
                "🌊 Public stream started"
            )

            ollama_start = time.time()

            for chunk in stream_clean_response(
                prompt
            ):

                yield chunk + "\n"

            print(
                "🤖 Ollama generation time:",
                round(
                    time.time() - ollama_start,
                    2
                ),
                "seconds"
            )

            # ---------------------------------------------
            # FINAL MESSAGE
            # ---------------------------------------------

            yield json.dumps({
                "sources": sources,
                "type": "pdf",
                "done": True
            }) + "\n"

            print(
                "🌊 Public stream finished"
            )

        except Exception as e:

            print("\n" + "=" * 70)
            print(
                "❌ PUBLIC STREAMING ERROR"
            )
            print("=" * 70)

            print(
                "Error:",
                repr(e)
            )

            print("=" * 70)

            yield json.dumps({
                "error": "AI streaming failed",
                "done": True
            }) + "\n"

    print(
        "🌊 Public streaming prepared after:",
        round(
            time.time() - start_time,
            2
        ),
        "seconds"
    )

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson"
    )


# =========================================================
# AUTHENTICATED STREAMING CHAT
# =========================================================

@router.post("/stream")
def authenticated_chat_stream(
    request: ChatRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    )
):

    start_time = time.time()

    print("\n" + "=" * 70)
    print("🔐 AUTHENTICATED STREAMING CHAT REQUEST")
    print("=" * 70)

    print(
        "User:",
        current_user.full_name
    )

    print(
        "User ID:",
        current_user.id
    )

    print(
        "Question:",
        request.message
    )

    print(
        "File ID:",
        request.file_id
    )

    # =====================================================
    # GREETING
    # =====================================================

    if is_greeting(
        request.message
    ):

        print(
            "👋 Greeting detected."
        )

        print(
            "🚫 RAG search skipped."
        )

        answer = (
            "Welcome to the Ethiopia Statistical Service "
            "(ESS) AI Assistant. How can I help you today?"
        )

        save_history(
            db=db,
            user_id=current_user.id,
            message=request.message,
            response=answer,
            chat_type="llm"
        )

        def greeting_response():

            yield json.dumps({
                "response": answer,
                "sources": [],
                "type": "llm",
                "done": True
            }) + "\n"

        print(
            "⏱️ Greeting response time:",
            round(
                time.time() - start_time,
                4
            ),
            "seconds"
        )

        return StreamingResponse(
            greeting_response(),
            media_type="application/x-ndjson"
        )

    # =====================================================
    # IMPORTANT:
    # USE SHARED RETRIEVER
    # =====================================================

    print(
        "♻️ Using shared ESS Retriever instance"
    )

    # =====================================================
    # PDF RETRIEVAL
    # =====================================================

    pdf_start = time.time()

    raw_results = retriever.search(
        request.message,
        file_id=request.file_id
    )

    pdf_time = time.time() - pdf_start

    print(
        "📄 Authenticated PDF retrieval time:",
        round(
            pdf_time,
            2
        ),
        "seconds"
    )

    print(
        "Raw retrieval results:",
        len(raw_results)
    )

    # =====================================================
    # NO RESULTS
    # =====================================================

    if not raw_results:

        answer = (
            "The information was not found "
            "in the provided ESS documents."
        )

        print(
            "❌ No PDF results found"
        )

        save_history(
            db=db,
            user_id=current_user.id,
            message=request.message,
            response=answer,
            chat_type="pdf"
        )

        def no_result():

            yield json.dumps({
                "response": answer,
                "sources": [],
                "type": "pdf",
                "done": True
            }) + "\n"

        return StreamingResponse(
            no_result(),
            media_type="application/x-ndjson"
        )

    # =====================================================
    # SELECT BEST RESULTS
    # =====================================================

    question = request.message.strip()

    results = select_best_results(
        question,
        raw_results,
        max_results=3
    )

    print(
        "🎯 Final chunks selected:",
        len(results)
    )

    # =====================================================
    # SHOW SELECTED EVIDENCE
    # =====================================================

    print("\n" + "=" * 70)
    print("📚 SELECTED PDF EVIDENCE")
    print("=" * 70)

    for index, item in enumerate(
        results,
        start=1
    ):

        metadata = item.get(
            "metadata",
            {}
        )

        filename = (
            metadata.get("filename")
            or metadata.get("file_name")
            or metadata.get("source")
            or "ESS PDF"
        )

        page = metadata.get(
            "page",
            "unknown"
        )

        text = normalize_text(
            item.get("text", "")
        )

        print(
            f"\nChunk #{index}"
        )

        print(
            "Document:",
            filename
        )

        print(
            "Page:",
            page
        )

        print(
            "Text:",
            text[:500]
        )

    print("=" * 70)

    # =====================================================
    # BUILD PROMPT
    # =====================================================

    prompt = build_pdf_prompt(
        question,
        results
    )

    print(
        "Chunks sent:",
        len(results)
    )

    print(
        "Context / prompt length:",
        len(prompt)
    )

    # =====================================================
    # SOURCES
    # =====================================================

    sources = extract_sources(
        results
    )

    # =====================================================
    # GENERATOR
    # =====================================================

    def generate():

        full_answer = ""

        try:

            print(
                "\n🌊 Authenticated stream started"
            )

            ollama_start = time.time()

            # ---------------------------------------------
            # STREAM AI
            # ---------------------------------------------

            for chunk in stream_clean_response(
                prompt
            ):

                yield chunk + "\n"

                try:

                    parsed = json.loads(
                        chunk
                    )

                    piece = parsed.get(
                        "response",
                        ""
                    )

                    if isinstance(
                        piece,
                        str
                    ):

                        full_answer += piece

                except (
                    json.JSONDecodeError,
                    TypeError
                ):

                    pass

            print(
                "🤖 Ollama generation time:",
                round(
                    time.time() - ollama_start,
                    2
                ),
                "seconds"
            )

            # =================================================
            # FALLBACK
            # =================================================

            if not full_answer.strip():

                full_answer = (
                    "The AI did not return a response."
                )

            # =================================================
            # SAVE HISTORY
            # =================================================

            print(
                "\n💾 Preparing to save authenticated chat..."
            )

            print(
                "User ID:",
                current_user.id
            )

            print(
                "Message:",
                request.message
            )

            print(
                "Answer length:",
                len(full_answer)
            )

            save_history(
                db=db,
                user_id=current_user.id,
                message=request.message,
                response=full_answer,
                chat_type="pdf"
            )

            # =================================================
            # SEND SOURCES
            # =================================================

            yield json.dumps({
                "sources": sources,
                "type": "pdf",
                "done": True
            }) + "\n"

            print(
                "\n✅ Authenticated stream finished"
            )

            print(
                "✅ History processing finished"
            )

        except Exception as e:

            print("\n" + "=" * 70)
            print(
                "❌ AUTHENTICATED STREAMING ERROR"
            )
            print("=" * 70)

            print(
                "Error:",
                repr(e)
            )

            print("=" * 70)

            # =================================================
            # SAVE PARTIAL ANSWER
            # =================================================

            if full_answer.strip():

                print(
                    "💾 Attempting to save partial answer..."
                )

                save_history(
                    db=db,
                    user_id=current_user.id,
                    message=request.message,
                    response=full_answer,
                    chat_type="pdf"
                )

            yield json.dumps({
                "error": "AI streaming failed",
                "done": True
            }) + "\n"

    print(
        "🌊 Authenticated streaming prepared after:",
        round(
            time.time() - start_time,
            2
        ),
        "seconds"
    )

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson"
    )


# =========================================================
# AUTHENTICATED NON-STREAMING CHAT
# =========================================================

@router.post("")
def chat(
    request: ChatRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    )
):

    start_time = time.time()

    print("\n" + "=" * 70)
    print("🔐 AUTHENTICATED CHAT REQUEST")
    print("=" * 70)

    print(
        "User:",
        current_user.full_name
    )

    print(
        "User ID:",
        current_user.id
    )

    print(
        "Question:",
        request.message
    )

    print(
        "File ID:",
        request.file_id
    )

    result = ask_ai(
        request.message,
        file_id=request.file_id
    )

    end_time = time.time()

    print(
        "⏱️ AI processing time:",
        round(
            end_time - start_time,
            2
        ),
        "seconds"
    )

    # =====================================================
    # SAVE HISTORY
    # =====================================================

    save_history(
        db=db,
        user_id=current_user.id,
        message=request.message,
        response=result["answer"],
        chat_type=result.get(
            "type",
            "unknown"
        )
    )

    return {
        "user": current_user.full_name,
        "message": request.message,
        "response": result["answer"],
        "sources": result["sources"],
        "type": result.get(
            "type",
            "unknown"
        ),
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat()
    }


# =========================================================
# GET CHAT HISTORY
# =========================================================

@router.get("/history")
def get_history(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    )
):

    print("\n" + "=" * 70)
    print("🕘 LOADING CHAT HISTORY")
    print("=" * 70)

    print(
        "User:",
        current_user.full_name
    )

    print(
        "User ID:",
        current_user.id
    )

    try:

        history = (
            chat_history_service.get_user_history(
                db=db,
                user_id=current_user.id
            )
        )

        print(
            "History records:",
            len(history)
        )

        return history

    except Exception as e:

        print("\n" + "=" * 70)
        print(
            "❌ FAILED TO LOAD CHAT HISTORY"
        )
        print("=" * 70)

        print(
            "Error:",
            repr(e)
        )

        print("=" * 70)

        db.rollback()

        raise