import json


class Instance:
    value: int

    def __init__(self, value: int):
        self.value = value

    def to_json(self):
        return {"value": self.value}

    @classmethod
    def from_json(cls, data):
        return cls(json.loads(data)["value"])


class Solution:
    value: int

    def __init__(self, value: int):
        self.value = value

    def to_json(self):
        return {"value": self.value}

    @classmethod
    def from_json(cls, data: dict):
        return cls(json.loads(data)["value"])


def my_algorithm(instance: Instance) -> Solution:
    return Solution(instance.value + 1)


def my_feasibility(instance: Instance, solution: Solution) -> bool:
    return True


def my_scoring(instance: Instance, solution: Solution) -> float:
    return solution.value % 10
