from algoworkbench import compute, feasibility, score

@compute(project="test")
def add(a, b):
    return a + b

def test_compute():
    
    assert add(1, 2) == 3

