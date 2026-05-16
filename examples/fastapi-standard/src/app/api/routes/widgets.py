from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.db.models import Widget
from app.db.session import get_session
from app.schemas.widget import WidgetCreate, WidgetRead
from app.services.widgets import create_widget, list_widgets

SessionDependency = Annotated[Session, Depends(get_session)]

router = APIRouter(prefix="/widgets")


@router.get("/", response_model=list[WidgetRead])
def get_widgets(session: SessionDependency) -> list[Widget]:
    return list_widgets(session)


@router.post("/", response_model=WidgetRead, status_code=status.HTTP_201_CREATED)
def create_widget_endpoint(payload: WidgetCreate, session: SessionDependency) -> Widget:
    return create_widget(session, payload)
