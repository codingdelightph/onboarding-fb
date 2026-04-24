import pytest
import state

@pytest.fixture(autouse=True)
def clear_state():
    state._states.clear()
    yield
    state._states.clear()
