import base64
import json
from algobench.file_handling import convert_to_string, convert_from_string
from pydantic import BaseModel
import dill as pickle

    
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
    instance_json, data_type = convert_to_string(instance)
    assert instance_json == '{"value": 1}'
    assert data_type == "json"

def test_json_conversion_pydantic():
    instance = PydanticValidClass(value=1)
    instance_json, data_type = convert_to_string(instance)
    assert instance_json == '{"value":1}'
    assert data_type == "json"

def test_json_conversion_pickle_fallback():
    instance = InvalidClass()
    instance_json, data_type = convert_to_string(instance)
    assert instance_json == base64.b64encode(pickle.dumps(instance)).decode('utf-8')
    assert data_type == "pickle"

def test_convert_from_string():
    instance = ValidClass(2)
    instance_json, data_type = convert_to_string(instance)
    converted_instance = convert_from_string(instance_json, data_type, ValidClass)
    assert converted_instance.value == instance.value
    assert data_type == "json"

def test_convert_from_string_pickle():
    instance = NonSerializableClass()
    instance_json, data_type = convert_to_string(instance)
    converted_instance = convert_from_string(instance_json, data_type, ValidClass)
    assert converted_instance.value == instance.value
    assert data_type == "pickle"
