import pytest

from account_deletion_service import Account, AccountDeletionService


class AcceptedCaptcha:
    def captcha_verify(self, token, action, ip=None):
        assert action == "account_delete"
        return {"ok": True, "data": {"verified": True}}


class RejectedCaptcha:
    def captcha_verify(self, token, action, ip=None):
        raise RuntimeError("captcha rejected")


def test_deletion_revokes_every_session_and_records_audit_event():
    service = AccountDeletionService(AcceptedCaptcha())
    service.accounts["u1"] = Account("u1", "artist@example.com", ["a", "b", "c"], [{"amount": 12}])
    result = service.delete_account("u1", "captcha-token", "203.0.113.9")
    assert result == {"status": "deleted", "user_id": "u1", "sessions_revoked": 3}
    assert service.accounts["u1"].sessions == []
    assert service.accounts["u1"].deleted is True
    assert service.audit_log[0]["type"] == "account_deleted"


def test_rejected_captcha_keeps_account_active():
    service = AccountDeletionService(RejectedCaptcha())
    service.accounts["u2"] = Account("u2", "viewer@example.com", ["s1"])
    with pytest.raises(RuntimeError):
        service.delete_account("u2", "bad-token")
    assert service.accounts["u2"].deleted is False
    assert service.accounts["u2"].sessions == ["s1"]
