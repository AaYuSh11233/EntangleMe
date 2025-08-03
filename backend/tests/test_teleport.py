from app.quantum.teleport import teleport_classically

def test_state_zero():
    result = teleport_classically("0")
    assert "counts" in result

def test_state_one():
    result = teleport_classically("1")
    assert "counts" in result
