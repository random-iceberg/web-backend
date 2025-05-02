from datetime import datetime
from typing import override

from sqlalchemy import ForeignKey
from sqlalchemy import Column
from sqlalchemy import Table
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped as M
from sqlalchemy.orm import mapped_column as column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


model_feature_link = Table(
    "model_feature_link",
    Base.metadata,
    Column(
        "model_id",
        ForeignKey("model.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "feature_id",
        ForeignKey("feature.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Model(Base):
    __tablename__: str = "model"

    id: M[int] = column(primary_key=True)
    uuid: M[str] = column(unique=True)
    name: M[str] = column()
    algorithm: M[str] = column()
    created_at: M[datetime] = column(server_default=func.now())
    accuracy: M[float | None] = column()

    features: M[list["Feature"]] = relationship(secondary=model_feature_link)

    @override
    def __repr__(self) -> str:
        return f"Model(uuid={self.uuid!r}, name={self.name!r}, algorithm={self.algorithm!r})"


class Feature(Base):
    __tablename__: str = "feature"

    id: M[int] = column(primary_key=True)
    name: M[str] = column(unique=True)

    @override
    def __repr__(self) -> str:
        return f"Feature(name={self.name!r})"
