from dataclasses import dataclass

from algoworkbench import compute, feasibility, score

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
def check(items: list[Item], capacity: float) -> bool:
    return sum(item.weight for item in items) <= capacity

@score
def score(items: list[Item]) -> float:
    return sum(item.value for item in items)


items = [Item(weight=2, value=5), Item(weight=3, value=4), Item(weight=1, value=1), Item(weight=1, value=3)]
solve(items, 5)
solve(items, 8)