"""Mixin de versionado para optimistic locking."""

from __future__ import annotations

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column


class VersionMixin:
    """Agrega una columna ``version`` para deteccion de escrituras concurrentes.

    El cliente envía la ``version`` leída al momento de cargar el recurso;
    el use case rechaza la escritura con 409 si el registro ya cambió.
    """

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False, server_default="1")
