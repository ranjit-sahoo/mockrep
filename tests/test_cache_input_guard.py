from unittest.mock import patch
import pytest
from app import db

@pytest.mark.parametrize('sid',['', 'missing', '../etc/passwd', 'x'*10000, '0'*23, 'G'*24])
def test_malformed_session_key_never_opens_database(sid):
    with patch('app.db.accounts.Conn', side_effect=AssertionError('DB must not open')):
        assert db.load(sid) is None


def test_session_save_rejects_malformed_key_without_db():
    with patch('app.db.accounts.Conn', side_effect=AssertionError('DB must not open')):
        assert db.save('../wrong', {}) is None
