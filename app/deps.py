from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    subject = decode_access_token(token)
    if subject is None or not subject.isdigit():
        raise credentials_error
    user = db.get(models.User, int(subject))
    if user is None:
        raise credentials_error
    return user


def get_owned_client(client_id: int, user: models.User, db: Session) -> models.Client:
    """Fetch a client only if it belongs to the user (404 otherwise, to avoid leaking existence)."""
    client = db.get(models.Client, client_id)
    if client is None or client.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Client not found")
    return client
