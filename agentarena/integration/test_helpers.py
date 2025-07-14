import httpx
from sqlmodel import Session

from agentarena.arena.models import Contest

ARENA_URL = "http://localhost:8000/api"
ACTOR_URL = "http://localhost:8001/api"


def load_fixture(data: dict, url: str):
    response = httpx.post(url, json=data)
    if response.status_code == 200:
        obj = response.json()

        return obj["id"]
    else:
        raise Exception(
            f"Error loading fixture: {response.status_code} {response.text}"
        )


def make_agent(name: str, strategy_id: str, participant_id: str):
    data = {
        "strategy_id": strategy_id,
        "name": name,
        "participant_id": participant_id,
    }
    response = httpx.post(f"{ACTOR_URL}/agent/", json=data)
    if response.status_code == 200:
        obj = response.json()
        return obj["id"]
    else:
        raise Exception(f"Error making agent: {response.status_code} {response.text}")


async def make_contest(
    arena_id: str,
    participants: list[str],
    config: dict,
    session: Session,
):
    data = {
        "arena_id": arena_id,
        "participant_ids": participants,
        "player_positions": config["player_positions"],
        "player_inventories": config["player_inventories"],
    }
    response = httpx.post(f"{ARENA_URL}/contest/", json=data)
    if response.status_code == 200:
        obj = response.json()
        contest = session.get(Contest, obj["id"])
        assert contest is not None
        assert contest.arena is not None
        return contest
    else:
        raise Exception(f"Error making contest: {response.status_code} {response.text}")
