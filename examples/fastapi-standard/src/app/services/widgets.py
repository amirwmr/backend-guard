from __future__ import annotations

from sqlmodel import Session, select

from app.db.models import Widget
from app.schemas.widget import WidgetCreate


def list_widgets(session: Session) -> list[Widget]:
    statement = select(Widget).where(Widget.is_active.is_(True)).order_by(Widget.name)
    return list(session.exec(statement))


def create_widget(session: Session, payload: WidgetCreate) -> Widget:
    widget = Widget(name=payload.name, description=payload.description)
    session.add(widget)
    session.commit()
    session.refresh(widget)
    return widget
