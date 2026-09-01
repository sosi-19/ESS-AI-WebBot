
from datetime import datetime, timezone
import json
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.schemas.chat import ChatRequest
from app.dependencies.auth import get_current_user
from app.models.user import User

from app.services.ai_service import ask_ai, stream_ollama, is_greeting
from app.database.connection import get_db
from app.services.chat_history_service import chat_history_service

from app.rag.retriever import Retriever


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


# =========================================================
# HELPER: BUILD PDF PROMPT
# =========================================================

def build_pdf_prompt(question: str, results: list) -> str:

    context = "\n\n------------------------\n\n".join(
        item["text"]
        for item in results
    )

    prompt = f"""
You are an Ethiopian Statistical Service assistant.

Answer ONLY using the provided PDF context.

Rules:

- If the question asks for a summary, provide the main findings of the report.
- Include important indicators, trends, and key changes from the report.
- Do not focus on only one table or one number.
- If the question asks for a specific rate or value, return the exact value from the context.
- Do not guess or use information outside the PDF context.
- If the information is not in the context, say:
  "The information was not found in the provided ESS documents."

Context:
{context}

Question:
{question}

Answer with only the final answer and a short explanation.
"""

    return prompt


# =========================================================
# HELPER: EXTRACT SOURCES
# =========================================================

def extract_sources(results: list) -> list:

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
# HELPER: SAVE CHAT HISTORY
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
# HELPER: NORMALIZE OLLAMA STREAM
# =========================================================
#
# Ollama normally returns chunks like:
#
# {"model":"qwen2.5:1.5b","response":"1","done":false}
#
# We DO NOT want to send this directly to the frontend.
#
# Instead we send:
#
# {"response":"1","done":false}
#
# At the end:
#
# {"sources":[...],"type":"pdf","done":true}
#
# =========================================================

def normalize_ollama_chunk(chunk):

    if chunk is None:
        return None

    # -----------------------------------------------------
    # If already a dictionary
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
    # Convert to string
    # -----------------------------------------------------

    if not isinstance(chunk, str):
        chunk = str(chunk)

    chunk = chunk.strip()

    if not chunk:
        return None

    # -----------------------------------------------------
    # Try to parse JSON returned by Ollama
    # -----------------------------------------------------

    try:

        parsed = json.loads(chunk)

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

        # -------------------------------------------------
        # If stream_ollama already returns plain text
        # -------------------------------------------------

        pass

    # -----------------------------------------------------
    # Raw text fallback
    # -----------------------------------------------------

    return {
        "response": chunk,
        "done": False
    }


# =========================================================
# HELPER: STREAM AI RESPONSE
# =========================================================

def stream_clean_response(prompt: str):

    """
    Reads the raw Ollama stream and converts it into
    clean ESS AI JSON chunks.

    Example input:

        {"model":"qwen2.5:1.5b","response":"13","done":false}

    Example output:

        {"response":"13","done":false}
    """

    for raw_chunk in stream_ollama(prompt):

        parsed = normalize_ollama_chunk(
            raw_chunk
        )

        if parsed is None:
            continue

        # Do not forward Ollama's internal metadata.
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

    if is_greeting(request.message):

        print("👋 Greeting detected.")
        print("🚫 RAG search skipped.")

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
    # RETRIEVER
    # =====================================================

    retriever = Retriever()

    # =====================================================
    # PDF RETRIEVAL
    # =====================================================

    pdf_start = time.time()

    results = retriever.search(
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

    # =====================================================
    # NO RESULTS
    # =====================================================

    if not results:

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
    # BUILD PROMPT
    # =====================================================

    question = request.message.strip()

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

            # ---------------------------------------------
            # STREAM CLEAN AI RESPONSE
            # ---------------------------------------------

            for chunk in stream_clean_response(
                prompt
            ):

                yield chunk + "\n"

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

    if is_greeting(request.message):

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
    # RETRIEVER
    # =====================================================

    retriever = Retriever()

    # =====================================================
    # PDF RETRIEVAL
    # =====================================================

    pdf_start = time.time()

    results = retriever.search(
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

    # =====================================================
    # NO RESULTS
    # =====================================================

    if not results:

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
    # BUILD PROMPT
    # =====================================================

    question = request.message.strip()

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

            # ---------------------------------------------
            # STREAM AI
            # ---------------------------------------------

            for chunk in stream_clean_response(
                prompt
            ):

                # Send clean chunk to frontend
                yield chunk + "\n"

                # -----------------------------------------
                # SAVE RESPONSE TEXT
                # -----------------------------------------

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
