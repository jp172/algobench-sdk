import os
import pytest
import requests
from algobench.decorator import algorithm
import time
import dotenv

dotenv.load_dotenv()

from tests.e2e_env import Instance, my_algorithm, my_feasibility, my_scoring

ENDPOINT = os.getenv("ENDPOINT")
API_KEY = os.getenv("API_KEY")
headers = {"Authorization": f"ApiKey {API_KEY}"}

                
def test_api_key_validation():
    response = requests.get(f"{ENDPOINT}/api/environments", headers=headers)
    assert response.status_code == 200

def test_api_key_validation_invalid():
    response = requests.get(f"{ENDPOINT}/api/environments", headers={"Authorization": "ApiKey invalid_key"})
    assert response.status_code == 403


def clear_test_environment():
    response = requests.get(f"{ENDPOINT}/api/environments", headers=headers)
    if response.status_code == 200:
        for env in response.json():
            if env["name"] in ["e2e_test_env", "e2e_test_env_with_solution_pull"]:
                requests.delete(f"{ENDPOINT}/api/environments/{env['id']}/", headers=headers)


@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup
    clear_test_environment()
    yield
    # Teardown
    clear_test_environment()


def test_full_decorator_flow():

    # Apply the decorator
    decorated_algo = algorithm(
        name="e2e_test_env",
        feasibility_function=my_feasibility,
        scoring_function=my_scoring,
        API_KEY=API_KEY,
        is_minimization=True
    )(my_algorithm)

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
    assert result.value == 6

    # Verify instance was created
    response = requests.get(f"{ENDPOINT}/api/instances/?environment__id={test_env['id']}", headers=headers)
    assert response.status_code == 200
    instances = response.json()
    assert len(instances) == 1
    test_instance = instances[0]
    assert test_instance["content"] == test_input.to_json()

    # Verify result was created
    response = requests.get(f"{ENDPOINT}/api/solutions/?instance__id={test_instance['id']}", headers=headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["content"] == result.to_json()

    result = decorated_algo(test_input)
    response = requests.get(f"{ENDPOINT}/api/instances/?environment__id={test_env['id']}", headers=headers)
    assert response.status_code == 200
    instances = response.json()
    assert len(instances) == 2
    

def test_full_decorator_flow_with_solution_pull():
    # Apply the decorator
    decorated_algo = algorithm(
        name="e2e_test_env_with_solution_pull",
        feasibility_function=my_feasibility,
        scoring_function=my_scoring,
        API_KEY=API_KEY,
        is_minimization=False,
        additional_wait_seconds=30
    )(my_algorithm)

    time.sleep(1)

    response = requests.get(f"{ENDPOINT}/api/environments/", headers=headers)
    assert response.status_code == 200
    environments = response.json()
    test_env = next((env for env in environments if env["name"] == "e2e_test_env_with_solution_pull"), None)
    assert test_env is not None

    result = decorated_algo(Instance(4))

    assert result.value == 9
    
    
    
    

