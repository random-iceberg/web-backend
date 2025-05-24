from datetime import datetime
from typing import override

from sqlalchemy import ForeignKey
from sqlalchemy import Column
from sqlalchemy import Table
from sqlalchemy import func
from sqlalchemy import JSON
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


class Prediction(Base):
    """Stores prediction history with input data and results"""
    __tablename__: str = "prediction"

    id: M[int] = column(primary_key=True)
    created_at: M[datetime] = column(server_default=func.now())
    input_data: M[dict] = column(JSON)  # Store PassengerData
    result: M[dict] = column(JSON)      # Store PredictionResult
    # TODO: Add user_id for authentication later
    
    @override
    def __repr__(self) -> str:
        return f"Prediction(id={self.id!r}, created_at={self.created_at!r})"
    

class User(Base):
    """Stores user information"""
    __tablename__ = "users"

    id: M[int] = column(primary_key=True, autoincrement=True)
    email: M[str] = column(unique=True, nullable=False)
    hashed_password: M[str] = column(nullable=False)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"
