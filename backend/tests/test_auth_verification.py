from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models.user import User
from app.services.auth import create_email_verification_code, create_user, verify_email_code


class EmailVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        Base.metadata.drop_all(self.engine)

    def test_new_user_requires_email_verification(self) -> None:
        with Session(self.engine) as db:
            user = create_user(db=db, email="new@example.com", password="password1")

            self.assertFalse(user.is_email_verified)

    def test_email_verification_code_confirms_user(self) -> None:
        with Session(self.engine) as db:
            user = create_user(db=db, email="verify@example.com", password="password1")
            code = create_email_verification_code(db=db, user=user)

            self.assertFalse(verify_email_code(db=db, user=user, code="000000"))
            verified = verify_email_code(db=db, user=db.get(User, user.id), code=code)

            self.assertTrue(verified)
            self.assertTrue(db.get(User, user.id).is_email_verified)


if __name__ == "__main__":
    unittest.main()
