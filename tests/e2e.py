import os
import pytest
import requests
import time
import dotenv
import logging

from algobench.decorator import algorithm
from tests.e2e_env import Instance, my_algorithm, my_feasibility, my_scoring

logger = logging.getLogger(__name__)

dotenv.load_dotenv()

ENDPOINT = os.getenv("ENDPOINT")
API_KEY = os.getenv("API_KEY")
headers = {"Authorization": f"ApiKey {API_KEY}"}


def test_api_key_validation():
    try:
        response = requests.get(f"{ENDPOINT}/api/problems", headers=headers)
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        assert False, "Connection error when validating API key"


def test_api_key_validation_invalid():
    try:
        response = requests.get(f"{ENDPOINT}/api/problems", headers={"Authorization": "ApiKey invalid_key"})
        assert response.status_code == 403
    except requests.exceptions.ConnectionError:
        assert False, "Connection error when validating invalid API key"


def clear_test_problem():
    try:
        response = requests.get(f"{ENDPOINT}/api/problems", headers=headers)
        if response.status_code == 200:
            for env in response.json():
                if env["name"] in ["e2e_test_env", "e2e_test_env_with_solution_pull"]:
                    requests.delete(f"{ENDPOINT}/api/problems/{env['id']}/", headers=headers)
    except requests.exceptions.ConnectionError:
        logger.warning("Connection error when clearing test problem")


@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup
    clear_test_problem()
    yield
    # Teardown
    clear_test_problem()


def test_full_decorator_flow():

    # Apply the decorator
    decorated_algo = algorithm(
        name="e2e_test_env",
        feasibility_function=my_feasibility,
        scoring_function=my_scoring,
        api_key=API_KEY,
        is_minimization=True,
    )(my_algorithm)

    # Give the server a moment to process the problem creation
    time.sleep(1)

    # Verify problem was created
    try:
        response = requests.get(f"{ENDPOINT}/api/problems/", headers=headers)
        assert response.status_code == 200
        problems = response.json()
        test_env = next((env for env in problems if env["name"] == "e2e_test_env"), None)
    except requests.exceptions.ConnectionError:
        assert False, "Connection error when validating problem"
    assert test_env is not None

    # Run the decorated algorithm
    test_input = Instance(5)
    result = decorated_algo(test_input)

    # Verify the result
    assert result.value == 6

    # Verify instance was created
    response = requests.get(f"{ENDPOINT}/api/instances/?problem__id={test_env['id']}", headers=headers)
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
    response = requests.get(f"{ENDPOINT}/api/instances/?problem__id={test_env['id']}", headers=headers)
    assert response.status_code == 200
    instances = response.json()
    assert len(instances) == 2


def test_full_decorator_flow_with_solution_pull():
    # Apply the decorator
    decorated_algo = algorithm(
        name="e2e_test_env_with_solution_pull",
        feasibility_function=my_feasibility,
        scoring_function=my_scoring,
        api_key=API_KEY,
        is_minimization=False,
        additional_wait_seconds=30,
    )(my_algorithm)

    time.sleep(1)

    try:
        response = requests.get(f"{ENDPOINT}/api/problems/", headers=headers)
        assert response.status_code == 200
        problems = response.json()
        test_env = next((env for env in problems if env["name"] == "e2e_test_env_with_solution_pull"), None)
    except requests.exceptions.ConnectionError:
        assert False, "Connection error when validating problem"
    assert test_env is not None

    result = decorated_algo(Instance(4))

    assert result.value == 9
