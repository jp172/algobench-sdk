import json
from algobench.file_handling import convert_to_json, convert_from_json
from pydantic import BaseModel


class PydanticValidClass(BaseModel):
    value: int


class ValidClass:
    def __init__(self, value: int = 1):
        self.value = value

    def to_json(self):
        return {"value": self.value}

    @classmethod
    def from_json(cls, json_string):
        data = json.loads(json_string)
        return cls(value=data["value"])


class NonSerializableClass:
    def __init__(self):
        self.value = 3


class InvalidClass:
    def __init__(self):
        self.non_serializable = NonSerializableClass()


def test_json_conversion():
    instance = ValidClass()
    instance_json = convert_to_json(instance)
    assert instance_json == '{"value": 1}'


def test_json_conversion_pydantic():
    instance = PydanticValidClass(value=1)
    instance_json = convert_to_json(instance)
    assert instance_json == '{"value":1}'
    assert instance == convert_from_json(instance_json, PydanticValidClass)


def test_convert_from_json():
    instance = ValidClass(2)
    instance_json = convert_to_json(instance)
    converted_instance = convert_from_json(instance_json, ValidClass)
    assert converted_instance.value == instance.value
