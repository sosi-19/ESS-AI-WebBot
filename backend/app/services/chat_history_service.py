from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory


class ChatHistoryService:

    # =====================================================
    # SAVE CHAT
    # =====================================================

    def save_chat(
        self,
        db: Session,
        user_id: int,
        message: str,
        response: str,
        chat_type: str
    ):

        try:

            chat = ChatHistory(
                user_id=user_id,
                message=message,
                response=response,
                type=chat_type
            )

            db.add(chat)

            db.commit()

            db.refresh(chat)

            print(
                f"✅ Chat saved successfully "
                f"(user_id={user_id}, chat_id={chat.id})"
            )

            return chat

        except Exception as e:

            print(
                f"❌ Error saving chat "
                f"(user_id={user_id}):",
                repr(e)
            )

            db.rollback()

            raise


    # =====================================================
    # GET USER CHAT HISTORY
    # =====================================================

    def get_user_history(
        self,
        db: Session,
        user_id: int
    ):

        try:

            chats = (
                db.query(ChatHistory)
                .filter(
                    ChatHistory.user_id == user_id
                )
                .order_by(
                    ChatHistory.created_at.desc()
                )
                .all()
            )

            print(
                f"📚 Loaded {len(chats)} chats "
                f"for user_id={user_id}"
            )

            return chats

        except Exception as e:

            print(
                f"❌ Error loading chat history "
                f"(user_id={user_id}):",
                repr(e)
            )

            db.rollback()

            raise


# =========================================================
# SERVICE INSTANCE
# =========================================================

chat_history_service = ChatHistoryService()