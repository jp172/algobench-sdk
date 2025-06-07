# algobench SDK

Improve solutions for your optimization problem by adding a single decorator to your code.

- Your optimization problem will be submitted to algobench to generate improved solution algorithms.
- While your code solves an instance, algobench delivers improved solutions on-the-fly.
- Visit [algobench.io](https://algobench.io) to check your optimization problems.

## Installation

```bash
pip install algobench
```

## Prerequisites

Generally, we consider any problem of the form

```python
def solve(instance: Instance) -> Solution:
    # do some complicated computation here
```

A computed solution should be feasible, i.e. pass some checks defined by

```python
def feasible(instance: Instance, solution: Solution) -> bool:
    # check feasibility of solution
```

and for a feasible solution a score is determined by

```python
def score(instance: Instance, solution: Solution) -> float:
    # compute score of the solution
```

These three functions, together with definitions of `Instance` and `Solution` make up the optimization problem.

Once you wrote your optimization problem, apply algobench's decorator to the algorithm function.

```python
@algorithm(
    name="Optimization Problem Name",
    feasibility_function=feasible,
    scoring_function=score,
    api_key="API_KEY",
    is_minimization=False,
    additional_wait_seconds=2)
def solve(instance: Instance) -> Solution:
    # do some complicated computation here
```

- Obtain your API key from [algobench.io](https://algobench.io)
- Specify whether you want to maximize or minimize the scoring function via `is_minimization`
- With `additional_wait_seconds` you can specify how many more seconds you want to wait for algobench after your local algorithm has computed its solution.

## Usage example (Knapsack Problem)

```python
from pydantic import BaseModel
from algobench import algorithm


class Item(BaseModel):
    id: int
    weight: float
    value: float


class Instance(BaseModel):
    items: dict[int, Item]
    capacity: float


class Solution(BaseModel):
    chosen_items: set[int]


def check(instance: Instance, solution: Solution) -> bool:
    if not set(instance.items.keys()).issuperset(solution.chosen_items):
        return False
    return (
        sum(instance.items[i].weight for i in solution.chosen_items)
        <= instance.capacity
    )


def score(instance: Instance, solution: Solution) -> float:
    return sum(instance.items[i].value for i in solution.chosen_items)


@algorithm(
    name="Knapsack-new",
    feasibility_function=check,
    scoring_function=score,
    api_key=API_KEY,
    is_minimization=False,
    additional_wait_seconds=2,
)
def solve(instance: Instance) -> Solution:
    remaining_capacity = instance.capacity
    chosen_ids = set()
    for item in sorted(
        instance.items.values(), key=lambda item: -item.value / item.weight
    ):
        if item.weight <= remaining_capacity:
            chosen_ids.add(item.id)
            remaining_capacity -= item.weight
    return Solution(chosen_items=chosen_ids)


def main():
    items = {
        1: Item(id=1, weight=1, value=1.5),
        2: Item(id=2, weight=2, value=2),
        3: Item(id=3, weight=3, value=3),
    }
    instance_1 = Instance(items=items, capacity=5)

    result = solve(instance_1)
    print(check(instance_1, result), score(instance_1, result))


if __name__ == "__main__":
    main()
```

Initially we use a greedy algorithm to solve the knapsack problem, which results in item 1 and 2 being chosen. What you can see from the second run is that in the background, algobench evolved a better algorithm using an automated evolutionary process and computed the optimal solution, which is to choose items 2 and 3.

## Requirements and (current) limitations
- The whole optimization problem needs to be contained in a single python file.
- All classes need to be convertible to and from json.

