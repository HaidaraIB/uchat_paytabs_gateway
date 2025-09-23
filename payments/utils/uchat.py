from django.conf import settings
import requests
import logging

logger = logging.getLogger("payments")


def change_plan(workspace_id: int, owner_email: str, plan_id: str):
    # Get workspace
    response = requests.get(
        url=f"{settings.UCHAT_BASE_URL}/workspace/{workspace_id}",
        headers={
            "authorization": f"Bearer {settings.UCHAT_TOKEN}",
        },
    )
    workspace = safe_json(response)
    logger.info("Workspace: %s", workspace)

    # If workspace not found or error, create it
    if not workspace or workspace.get("status") != "ok":
        response = requests.post(
            url=f"{settings.UCHAT_BASE_URL}/workspace/create-for-existing-user",
            json={
                "email": owner_email,
                "team_name": owner_email,
                "template_ns": owner_email,
                "trial_days": 14,
            },
            headers={"authorization": f"Bearer {settings.UCHAT_TOKEN}"},
        )
        workspace = safe_json(response)
        logger.info("Workspace Created: %s", workspace)
        if not workspace or workspace.get("status") != "ok":
            return False

    workspace_id = workspace["data"]["id"]

    # Change plan
    response = requests.post(
        url=f"{settings.UCHAT_BASE_URL}/workspace/{workspace_id}/change-plan",
        json={"plan": plan_id},
        headers={
            "authorization": f"Bearer {settings.UCHAT_TOKEN}",
        },
    )
    change_plan_res = safe_json(response)
    logger.info("Change Plan Response: %s", change_plan_res)
    if change_plan_res.get("status", None) == "ok":
        return workspace_id
    return False


def safe_json(response: requests.Response):
    """Try to parse JSON, return None if empty or invalid."""
    try:
        return response.json()
    except ValueError:
        logger.warning(
            "Response not JSON. Status: %s, Body: %s",
            response.status_code,
            response.text,
        )
        return {}
