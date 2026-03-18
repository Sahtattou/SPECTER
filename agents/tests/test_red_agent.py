from app.chains.red_injector_chain import run_red_injector_chain


def test_red_agent_scaffold() -> None:
    assert run_red_injector_chain()
