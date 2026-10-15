from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


@dataclass
class Account:
    user_id: str
    email: str
    sessions: List[str] = field(default_factory=list)
    payment_events: List[dict] = field(default_factory=list)
    deleted: bool = False


class AccountDeletionService:
    def __init__(self, captcha_client):
        self.captcha_client = captcha_client
        self.accounts: Dict[str, Account] = {}
        self.audit_log: List[dict] = []

    def delete_account(self, user_id: str, captcha_token: str, ip: str = None) -> dict:
        account = self.accounts[user_id]
        if account.deleted:
            return {"status": "already_deleted", "user_id": user_id}
        self.captcha_client.captcha_verify(captcha_token, "account_delete", ip)
        revoked = len(account.sessions)
        account.sessions.clear()
        account.deleted = True
        event = {
            "user_id": user_id,
            "type": "account_deleted",
            "sessions_revoked": revoked,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        self.audit_log.append(event)
        return {"status": "deleted", "user_id": user_id, "sessions_revoked": revoked}


def demo():
    from infrai_client import InfraiClient

    service = AccountDeletionService(InfraiClient())
    service.accounts["creator-42"] = Account("creator-42", "creator@example.com", ["s1", "s2"])
    print(service.delete_account("creator-42", os.environ["CAPTCHA_TOKEN"]))


if __name__ == "__main__":
    import os
    demo()
