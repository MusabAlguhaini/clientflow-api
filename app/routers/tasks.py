from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user, get_owned_client

router = APIRouter(tags=["tasks"])


def _get_owned_task(task_id: int, user: models.User, db: Session) -> models.Task:
    task = db.get(models.Task, task_id)
    if task is None or task.client.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/clients/{client_id}/tasks", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    client_id: int,
    payload: schemas.TaskCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = get_owned_client(client_id, user, db)
    task = models.Task(client_id=client.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks", response_model=list[schemas.TaskOut])
def list_tasks(
    status_filter: models.TaskStatus | None = Query(default=None, alias="status"),
    priority: models.TaskPriority | None = None,
    client_id: int | None = None,
    overdue: bool = Query(default=False, description="Only tasks past their due date and not done"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(models.Task).join(models.Client).where(models.Client.owner_id == user.id)
    if status_filter:
        stmt = stmt.where(models.Task.status == status_filter)
    if priority:
        stmt = stmt.where(models.Task.priority == priority)
    if client_id:
        stmt = stmt.where(models.Task.client_id == client_id)
    if overdue:
        stmt = stmt.where(models.Task.due_date < date.today(), models.Task.status != models.TaskStatus.done)
    stmt = stmt.order_by(models.Task.id).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.get("/tasks/summary", response_model=schemas.Summary)
def summary(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    owned = select(models.Client.id).where(models.Client.owner_id == user.id)
    clients = db.scalar(select(func.count()).select_from(owned.subquery())) or 0
    rows = db.execute(
        select(models.Task.status, func.count())
        .where(models.Task.client_id.in_(owned))
        .group_by(models.Task.status)
    ).all()
    by_status = {s.value: 0 for s in models.TaskStatus}
    for st, count in rows:
        by_status[st.value] = count
    overdue = db.scalar(
        select(func.count())
        .select_from(models.Task)
        .where(
            models.Task.client_id.in_(owned),
            models.Task.due_date < date.today(),
            models.Task.status != models.TaskStatus.done,
        )
    ) or 0
    return schemas.Summary(
        clients=clients, tasks_total=sum(by_status.values()), tasks_by_status=by_status, overdue_tasks=overdue
    )


@router.get("/tasks/{task_id}", response_model=schemas.TaskOut)
def get_task(task_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned_task(task_id, user, db)


@router.patch("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: int,
    payload: schemas.TaskUpdate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = _get_owned_task(task_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = _get_owned_task(task_id, user, db)
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
