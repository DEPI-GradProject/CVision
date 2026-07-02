import logging

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from auth.db import get_user_db
from config import settings
from models.db_models import User

logger = logging.getLogger(__name__)

bearer_transport = BearerTransport(tokenUrl="auth/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.auth_jwt_secret,
        lifetime_seconds=settings.auth_jwt_lifetime_seconds,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.auth_jwt_secret
    verification_token_secret = settings.auth_jwt_secret

    async def on_after_register(self, user: User, request: Request | None = None):
        logger.info("User %s (%s) registered", user.id, user.email)

    async def on_after_login(self, user: User, request: Request | None = None):
        logger.info("User %s (%s) logged in", user.id, user.email)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
