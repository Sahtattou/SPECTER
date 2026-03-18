from app.chains.red_injector_chain import run_red_injector_chain


class FakeClient:
    def get_recent_events(self, limit: int = 100, stage: str | None = None):
        return [{"ioc_value": "198.51.100.2", "ioc_type": "ip", "corroboration_count": 2}]

    def submit_synthetic_event(self, payload: dict):
        return {"submitted": True, "payload": payload}


def test_red_agent_dry_run_does_not_submit() -> None:
    result = run_red_injector_chain(client=FakeClient(), attack_type="GHOST_DOMAIN", dry_run=True)

    assert result.attack_type == "GHOST_DOMAIN"
    assert result.submitted is False
    assert result.payload.get("is_synthetic") is True


def test_red_agent_submit_calls_client() -> None:
    result = run_red_injector_chain(client=FakeClient(), attack_type="REPUTATION_LAUNDERING", dry_run=False)

    assert result.submitted is True
    assert result.payload.get("ioc_type") == "ip"
