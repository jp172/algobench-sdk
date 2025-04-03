import pytest
import requests
from algobench.decorator import algorithm
import time

ENDPOINT = "http://localhost:8000"
API_KEY = "63ce7ccbb74332c5e0ed457550f5dde553ce57d4c9affca415384333fb8b18c1267295aed79818ec"
headers = {"Authorization": f"ApiKey {API_KEY}"}

                

def test_api_key_validation():
    response = requests.get(f"{ENDPOINT}/api/environments", headers=headers)
    assert response.status_code == 200

def test_api_key_validation_invalid():
    response = requests.get(f"{ENDPOINT}/api/environments", headers={"Authorization": "ApiKey invalid_key"})
    assert response.status_code == 403


def clear_test_environment():
    """Helper function to clean up test environment if it exists"""
    response = requests.get(f"{ENDPOINT}/api/environments", headers=headers)
    if response.status_code == 200:
        for env in response.json():
            if env["name"] == "e2e_test_env":
                requests.delete(f"{ENDPOINT}/api/environments/{env['id']}/", 
                             headers=headers)

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup
    clear_test_environment()
    yield
    # Teardown
    clear_test_environment()


class Instance:
    value: int
    def __init__(self, value: int):
        self.value = value
    def to_json(self):
        return {'value': self.value}
    def from_json(self, json: dict):
        self.value = json["value"]

class Solution:
    value: int
    def __init__(self, value: int):
        self.value = value
    def to_json(self):
        return {'value': self.value}
    def from_json(self, json: dict):
        self.value = json["value"]

def test_full_decorator_flow():
    def test_algorithm(instance: Instance) -> Solution:
        return Solution(instance.value * 2)

    def test_feasibility(instance: Instance, solution: Solution) -> bool:
        return True

    def test_scoring(instance: Instance, solution: Solution) -> float:
        return solution.value

    # Apply the decorator
    decorated_algo = algorithm(
        test_algorithm,
        name="e2e_test_env",
        feasibility_function=test_feasibility,
        scoring_function=test_scoring,
        API_KEY=API_KEY,
        is_minimization=True
    )

    # Give the server a moment to process the environment creation
    time.sleep(1)

    # Verify environment was created
    response = requests.get(f"{ENDPOINT}/api/environments/", headers=headers)
    assert response.status_code == 200
    environments = response.json()
    test_env = next((env for env in environments if env["name"] == "e2e_test_env"), None)
    assert test_env is not None

    # Run the decorated algorithm
    test_input = Instance(5)
    result = decorated_algo(test_input)
    
    # Verify the result
    assert result.value == 10

    # Verify instance was created
    response = requests.get(f"{ENDPOINT}/api/instances/?environment__id={test_env['id']}", headers=headers)
    assert response.status_code == 200
    instances = response.json()
    assert len(instances) == 1
    test_instance = instances[0]
    assert test_instance["content"].replace("'", '"') == str(test_input.to_json()).replace("'", '"')

    # Verify result was created
    response = requests.get(f"{ENDPOINT}/api/solutions/?instance__id={test_instance['id']}", headers=headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["content"].replace("'", '"') == str(result.to_json()).replace("'", '"')

    result = decorated_algo(test_input)
    response = requests.get(f"{ENDPOINT}/api/instances/?environment__id={test_env['id']}", headers=headers)
    assert response.status_code == 200
    instances = response.json()
    assert len(instances) == 2
    
    
    
    
    
    
    

