import pytest
import json
from unittest.mock import patch

from algobench.api_client import APIClient


@pytest.fixture
def mock_requests():
    with patch("algobench.api_client.requests") as mock_req:
        yield mock_req


@pytest.fixture
def api_client(mock_requests):
    with patch("algobench.api_client.requests") as mock_req:
        mock_req.get.return_value.status_code = 200
        client = APIClient(api_key="test_key", env_name="test_env")
        return client


class SampleClass:

    def __init__(self, data: str = "test"):
        self.data = data

    def to_json(self):
        return {"data": self.data}

    @classmethod
    def from_json(cls, json_string):
        return cls(json.loads(json_string)["data"])


class NonSerializableClass:
    def __init__(self):
        self.data = "test"


def test_check_api_key_empty():
    client = APIClient(api_key="", env_name="test_env")
    assert client.login() is False


def test_check_api_key_invalid():
    with patch("algobench.api_client.requests") as mock_req:
        mock_req.get.return_value.status_code = 401
        client = APIClient(api_key="invalid_key", env_name="test_env")
        assert client.login() is False


def test_check_api_key_valid():
    with patch("algobench.api_client.requests") as mock_req:
        mock_req.get.return_value.status_code = 200
        client = APIClient(api_key="valid_key", env_name="test_env")
        assert client.login() is True


def test_upload_input_single_arg(api_client, mock_requests):
    instance = SampleClass()
    mock_requests.post.return_value.status_code = 201
    mock_requests.post.return_value.json.return_value = {"id": "test_id"}

    instance_id = api_client.upload_instance(instance)

    assert instance_id == "test_id"
    mock_requests.post.assert_called_once()


def test_upload_input_failed_request(api_client, mock_requests):
    instance = SampleClass()
    mock_requests.post.return_value.status_code = 400
    mock_requests.post.return_value.json.return_value = {"error": "test error"}

    instance_id = api_client.upload_instance(instance)

    assert instance_id is None
    mock_requests.post.assert_called_once()


def test_upload_solution_success(api_client, mock_requests):
    result = SampleClass()
    mock_requests.post.return_value.status_code = 201
    mock_requests.post.return_value.json.return_value = {"id": "result_id"}

    result_id = api_client.upload_solution(result, "test_instance_id", True, 1.0)

    assert result_id == "result_id"
    mock_requests.post.assert_called_once()


def test_upload_solution_failed_request(api_client, mock_requests):
    result = SampleClass()
    mock_requests.post.return_value.status_code = 400
    mock_requests.post.return_value.json.return_value = {"error": "test error"}

    result_id = api_client.upload_solution(result, "test_instance_id", True, 1.0)

    assert result_id is None
    mock_requests.post.assert_called_once()


def test_upload_problem(api_client, mock_requests):
    def test_algo(x):
        return x

    def test_feasibility(x):
        return True

    def test_scoring(x):
        return x

    mock_requests.get.return_value.status_code = 200
    mock_requests.get.return_value.json.return_value = []
    api_client.upload_problem(test_algo, test_feasibility, test_scoring, True)

    mock_requests.post.assert_called_once()
    called_json = mock_requests.post.call_args.kwargs["json"]
    assert "python_version" in called_json
    assert "code" in called_json
    assert "algorithm_function_name" in called_json
    assert "feasibility_function_name" in called_json
    assert "score_function_name" in called_json
    assert "name" in called_json


def test_update_problem(api_client, mock_requests):
    def test_algo(x):
        return x

    def test_feasibility(x):
        return True

    def test_scoring(x):
        return x

    mock_requests.get.return_value.status_code = 200
    mock_requests.get.return_value.json.return_value = [{"id": "test_id", "name": "test_env"}]
    api_client.problem_id = "test_id"
    api_client.upload_problem(test_algo, test_feasibility, test_scoring, True)
    mock_requests.put.assert_called_once()
    called_json = mock_requests.put.call_args.kwargs["json"]
    assert "python_version" in called_json
    assert "code" in called_json
    assert "algorithm_function_name" in called_json
    assert "feasibility_function_name" in called_json
    assert "score_function_name" in called_json
    assert "name" in called_json


def test_login(api_client, mock_requests):
    mock_requests.get.return_value.status_code = 200
    mock_requests.get.return_value.json.return_value = [
        {"name": "test_env", "id": "123"},
        {"name": "other_env", "id": "456"},
    ]
    assert api_client.login()
    assert api_client.problem_id == "123"


def test_pull_solution(api_client, mock_requests):
    mock_requests.get.return_value.status_code = 200
    mock_requests.get.return_value.json.return_value = {
        "id": "test_id",
        "content": {"data": "pull_solution_test_content"},
    }
    solution = api_client.pull_solution("test_instance_id", SampleClass)
    assert solution.data == "pull_solution_test_content"


def test_no_connection(api_client, mock_requests):
    # mock_requests.get.side_effect = requests.exceptions.ConnectionError
    assert api_client.login() is False
