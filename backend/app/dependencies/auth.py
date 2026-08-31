from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.core.security import SECRET_KEY, ALGORITHM


# ==================================================
# JWT Authentication
# ==================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )


    # ==================================================
    # Decode JWT
    # ==================================================

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")


        if not email:

            print("❌ JWT does not contain 'sub'")

            raise credentials_exception


    except JWTError as error:

        print(
            "❌ JWT validation error:",
            str(error)
        )

        raise credentials_exception


    # ==================================================
    # Find user
    # ==================================================

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


    if user is None:

        print(
            "❌ No user found for email:",
            email
        )

        raise credentials_exception


    print(
        "✅ Authenticated user:",
        user.email
    )


    return user