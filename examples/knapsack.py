from dataclasses import dataclass
from algoworkbench import compute, feasibility, score
from test import test
from examples.test_folder import another_test

@dataclass
class Item:
    weight: float
    value: float

@compute
def solve(items: list[Item], capacity: float) -> list[Item]:
    remaining_capacity = capacity
    ret = []
    for item in sorted(items, key=lambda item: -item.value / item.weight):
        if item.weight <= remaining_capacity:
            ret.append(item)
            remaining_capacity -= item.weight
    return ret

@feasibility
def check(solution: list[Item], capacity: float) -> bool:
    return sum(item.weight for item in solution) <= capacity

@score
def score(solution: list[Item]) -> float:
    return sum(item.value for item in solution)


items = [Item(weight=2, value=5), Item(weight=3, value=4), Item(weight=1, value=1), Item(weight=1, value=3)]
result = solve(items, 5)
print(check(result, 5), score(result))

solve(items, 8)
test()
another_test.another_test()