from backend.app.services import escalation_service


def test_wants_human_agent_by_phrase():
    assert escalation_service.wants_human_agent("Позовите оператора, ничего не работает")
    assert not escalation_service.wants_human_agent("Спасибо, всё понятно")


def test_wants_human_agent_explicit_flag():
    assert escalation_service.wants_human_agent("привет", request_human=True)
