from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user, get_owned_client

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=schemas.ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: schemas.ClientCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = models.Client(owner_id=user.id, **payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=list[schemas.ClientOut])
def list_clients(
    q: str | None = Query(default=None, description="Search by name or company"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(models.Client).where(models.Client.owner_id == user.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(models.Client.name.ilike(like) | models.Client.company.ilike(like))
    stmt = stmt.order_by(models.Client.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.get("/{client_id}", response_model=schemas.ClientOut)
def get_client(client_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_owned_client(client_id, user, db)


@router.patch("/{client_id}", response_model=schemas.ClientOut)
def update_client(
    client_id: int,
    payload: schemas.ClientUpdate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = get_owned_client(client_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = get_owned_client(client_id, user, db)
    db.delete(client)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
