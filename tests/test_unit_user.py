import sys
import pytest
import pathlib

# Add repo root to PYTHONPATH
repo_root = pathlib.Path(__file__).parent.parent.resolve()
sys.path.append(str(repo_root))

from services.user_service.app.auth import verify_password, get_password_hash, create_access_token, verify_token

class TestUserAuth:

    def test_password_hashing(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_jwt_token_creation(self):
        email = "test@example.com"
        token = create_access_token(data={"sub": email})
        token_data = verify_token(token)
        assert token_data.email == email  

    def test_invalid_token(self):
        with pytest.raises(Exception):
            verify_token("invalid_token")
