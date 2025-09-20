from ..models import Order
from django.conf import settings
import requests


def change_plan(workspace_id: int, owner_email: str, plan_id: int):
    workspace = requests.get(
        url=f"{settings.UCHAT_BASE_URL}/workspace/{workspace_id}",
        headers={
            "authorization": f"Bearer {settings.UCHAT_TOKEN}",
        },
    ).json()
    if not (workspace.get("status", False) == "ok"):
        workspace = requests.post(
            url=f"{settings.UCHAT_BASE_URL}/workspace/create-for-existing-user",
            json={
                "email": owner_email,
                "team_name": owner_email,
                "template_ns": owner_email,
                "trial_days": 14,
            },
            headers={
                "authorization": f"Bearer {settings.UCHAT_TOKEN}",
            },
        ).json()
        if not (workspace.get("status", False) == "ok"):
            # TODO error
            return
    workspace_id = workspace["data"]["id"]
    requests.post(
        url=f"{settings.UCHAT_BASE_URL}/workspace/{workspace_id}/change_plan",
        json={
            "plan": plan_id,
        },
        headers={
            "authorization": f"Bearer {settings.UCHAT_TOKEN}",
        },
    )
    return workspace_id
