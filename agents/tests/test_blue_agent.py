from app.chains.blue_analyst_chain import run_blue_analyst_chain


def test_blue_agent_scaffold() -> None:
    assert run_blue_analyst_chain()
