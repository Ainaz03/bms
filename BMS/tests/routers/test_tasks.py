import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.future import select

from app.main import app
from app.core.auth import current_active_user
from app.models.user import User, UserRole
from app.models.team import Team
from app.models.task import Task, TaskStatus
from app.models.comment import Comment
from app.models.evaluation import Evaluation


@pytest.mark.asyncio
async def test_create_task(async_client: AsyncClient, db_session):
    # 1) подготовка: менеджер + команда
    manager = User(
        email="mgr@example.com", hashed_password="x",
        role=UserRole.MANAGER, is_active=True,
        is_superuser=False, is_verified=True
    )
    db_session.add(manager)
    await db_session.commit()
    await db_session.refresh(manager)

    team = Team(name="T1", invite_code="C1", admin_id=manager.id)
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)

    # присвоим менеджеру team_id
    manager.team_id = team.id
    await db_session.commit()
    await db_session.refresh(manager)

    app.dependency_overrides[current_active_user] = lambda: manager

    payload = {
        "title": "Test Task",
        "description": "Desc",
        "deadline": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "assignee_id": manager.id,
        "status": "open",  # lowercase
    }
    resp = await async_client.post("/tasks/", json=payload)
    if resp.status_code != 201:
        print("PAYLOAD:", payload)
        print("ERROR DETAIL:", resp.status_code, resp.json())
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["title"] == "Test Task"
    assert data["creator_id"] == manager.id

    app.dependency_overrides.pop(current_active_user)


@pytest.mark.asyncio
async def test_update_and_delete_task(async_client: AsyncClient, db_session):
    # 1) подготовка: менеджер + команда + задача
    manager = User(
        email="mu@example.com", hashed_password="x",
        role=UserRole.MANAGER, team_id=1,
        is_active=True, is_superuser=False, is_verified=True
    )
    db_session.add(manager)
    await db_session.commit()
    await db_session.refresh(manager)

    task = Task(
        title="Old", description="d",
        deadline=datetime.utcnow(), creator_id=manager.id,
        assignee_id=manager.id, status=TaskStatus.OPEN
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    app.dependency_overrides[current_active_user] = lambda: manager

    upd = {
        "title": "New",
        "status": "done",          # lowercase
        "assignee_id": manager.id,
        "deadline": task.deadline.isoformat(),
    }
    resp_upd = await async_client.put(f"/tasks/{task.id}", json=upd)
    if resp_upd.status_code != 200:
        print("UPD PAYLOAD:", upd)
        print("ERROR DETAIL:", resp_upd.status_code, resp_upd.json())
    assert resp_upd.status_code == status.HTTP_200_OK
    out = resp_upd.json()
    assert out["title"] == "New"
    assert out["status"] == "done"

    # 3) удаление
    resp_del = await async_client.delete(f"/tasks/{task.id}")
    assert resp_del.status_code == status.HTTP_204_NO_CONTENT

    # проверяем, что нет в БД
    result = await db_session.execute(select(Task).where(Task.id == task.id))
    assert result.scalar_one_or_none() is None

    app.dependency_overrides.pop(current_active_user)


@pytest.mark.asyncio
async def test_comments_and_evaluations(async_client: AsyncClient, db_session):
    # подготовка: менеджер + команда + участник + задача DONE
    manager = User(
        email="m3@example.com", hashed_password="x",
        role=UserRole.MANAGER, team_id=3,
        is_active=True, is_superuser=False, is_verified=True
    )
    member = User(
        email="u3@example.com", hashed_password="x",
        role=UserRole.USER, team_id=3,
        is_active=True, is_superuser=False, is_verified=True
    )
    db_session.add_all([manager, member])
    await db_session.commit()
    await db_session.refresh(manager)
    await db_session.refresh(member)

    task = Task(
        title="TK", description="d",
        deadline=datetime.utcnow(),
        creator_id=manager.id,
        assignee_id=member.id,
        status=TaskStatus.DONE
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # а) комментарии как member
    app.dependency_overrides[current_active_user] = lambda: member
    resp_c = await async_client.post(
        f"/tasks/{task.id}/comments",
        json={"text": "Hello"}
    )
    assert resp_c.status_code == status.HTTP_201_CREATED
    assert resp_c.json()["text"] == "Hello"

    resp_list = await async_client.get(f"/tasks/{task.id}/comments")
    assert any(c["text"] == "Hello" for c in resp_list.json())

    # member не может ставить оценку
    resp_ev_forbid = await async_client.post(
        f"/tasks/{task.id}/evaluations", json={"score": 5}
    )
    assert resp_ev_forbid.status_code == status.HTTP_403_FORBIDDEN

    # б) оценки как manager
    app.dependency_overrides[current_active_user] = lambda: manager
    resp_ev = await async_client.post(
        f"/tasks/{task.id}/evaluations", json={"score": 4}
    )
    assert resp_ev.status_code == status.HTTP_201_CREATED
    assert resp_ev.json()["score"] == 4

    resp_ev_list = await async_client.get(f"/tasks/{task.id}/evaluations")
    assert any(e["score"] == 4 for e in resp_ev_list.json())

    app.dependency_overrides.pop(current_active_user)
