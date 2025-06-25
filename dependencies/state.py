from typing import Annotated, Protocol, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class RequestStateHolder(Protocol):
    async_session: async_sessionmaker[AsyncSession]
    jwt_key: str
    correlation_id: str


def get_request_state(request: Request) -> RequestStateHolder:
    return cast(RequestStateHolder, cast(object, request.state))


RequestState = Annotated[RequestStateHolder, Depends(get_request_state)]
