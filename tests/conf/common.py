from dataclasses import dataclass

from db.schemas import User
from models.schemas import UserCredentials

JWT_KEY = "test_jwt_key"


ADMIN_CREDS = UserCredentials(email="admin", password="admin_password")
TEST_CREDS = UserCredentials(email="test", password="test_password")

TEST_USERS_CREDS = {
    i: UserCredentials(email=f"test{i}", password=f"test{i}_password")
    for i in range(1, 4)
}


@dataclass
class UserData:
    creds: UserCredentials
    role: str
    user: User


@dataclass
class UserDataWithToken(UserData):
    token: str
