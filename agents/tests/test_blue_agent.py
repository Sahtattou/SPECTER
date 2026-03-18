from app.chains.blue_analyst_chain import run_blue_analyst_chain


class FakeClient:
    def get_recent_events(self, limit: int = 100, stage: str | None = None):
        return [
            {"ioc_value": "1.1.1.1", "threat_level": "HIGH", "composite_score": 72.5},
            {"ioc_value": "evil-login.example", "threat_level": "CRITICAL", "composite_score": 91.0},
            {"ioc_value": "2.2.2.2", "threat_level": "MEDIUM", "composite_score": 51.0},
        ]


def test_blue_agent_returns_summary_and_counts() -> None:
    result = run_blue_analyst_chain(client=FakeClient(), limit=10)

    assert result.total_events == 3
    assert result.by_threat_level["CRITICAL"] == 1
    assert len(result.top_iocs) > 0
    assert "Analyzed" in result.summary
