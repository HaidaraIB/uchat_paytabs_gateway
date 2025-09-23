from ..models import Order
from django.conf import settings
import requests
import logging

logger = logging.getLogger("payments")


def change_plan(workspace_id: int, owner_email: str, plan_id: str):
    try:
        workspace = requests.get(
            url=f"{settings.UCHAT_BASE_URL}/workspace/{workspace_id}",
            headers={
                "authorization": f"Bearer {settings.UCHAT_TOKEN}",
            },
        ).json()
        logger.info("Workspace: %s", workspace)
    except:
        return False
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
        logger.info("Workspace Created: %s", workspace)
        if not (workspace.get("status", False) == "ok"):
            return False
    workspace_id = workspace["data"]["id"]
    change_plan_res = requests.post(
        url=f"{settings.UCHAT_BASE_URL}/workspace/{workspace_id}/change_plan",
        json={
            "plan": plan_id,
        },
        headers={
            "authorization": f"Bearer {settings.UCHAT_TOKEN}",
        },
    ).json()
    logger.info("Change Plan Response: %s", change_plan_res)
    return workspace_id
