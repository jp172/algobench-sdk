from algobench.decorator import algorithm
from unittest.mock import Mock, patch


def sample_algorithm(x: int) -> int:
    return x * 2


def sample_feasibility(x: int, y: int) -> bool:
    return True


def sample_scoring(x: int, y: int) -> float:
    return x


def test_decorator_with_sample_functions():
    with patch("algobench.decorator.APIClient") as MockAPIClient:
        mock_client = Mock()
        mock_client.check_api_key.return_value = True
        mock_client.upload_instance.return_value = "test_instance_id"
        MockAPIClient.return_value = mock_client

        wrapped = algorithm(
            name="test_algo",
            feasibility_function=sample_feasibility,
            scoring_function=sample_scoring,
            api_key="valid_key",
            is_minimization=True,
        )(sample_algorithm)

        assert wrapped(5) == 10


def test_decorator_invalid_api_key():
    with patch("algobench.decorator.APIClient") as MockAPIClient:
        mock_client = Mock()
        mock_client.login.return_value = False
        MockAPIClient.return_value = mock_client

        wrapped = algorithm(
            name="test_algo",
            feasibility_function=sample_feasibility,
            scoring_function=sample_scoring,
            api_key="invalid_key",
            is_minimization=True,
        )(sample_algorithm)

        assert wrapped == sample_algorithm


def test_decorator_empty_name():
    with patch("algobench.decorator.APIClient") as MockAPIClient:
        mock_client = Mock()
        mock_client.login.return_value = True
        MockAPIClient.return_value = mock_client

        wrapped = algorithm(
            name="",
            feasibility_function=sample_feasibility,
            scoring_function=sample_scoring,
            api_key="valid_key",
            is_minimization=True,
        )(sample_algorithm)
        assert wrapped == sample_algorithm


def test_decorator_upload_failures():
    with patch("algobench.decorator.APIClient") as MockAPIClient:
        mock_client = Mock()
        mock_client.login.return_value = True
        mock_client.upload_instance.side_effect = Exception("Upload failed")
        MockAPIClient.return_value = mock_client

        wrapped = algorithm(
            name="test_algo",
            feasibility_function=sample_feasibility,
            scoring_function=sample_scoring,
            api_key="valid_key",
            is_minimization=True,
        )(sample_algorithm)

        assert wrapped(5) == 10
        assert wrapped != sample_algorithm
        mock_client.upload_instance.assert_called_once()


def test_decorator_persistence():
    with patch("algobench.decorator.APIClient") as MockAPIClient:
        mock_client = Mock()
        mock_client.login.return_value = True
        mock_client.upload_instance.return_value = "test_instance_id"
        MockAPIClient.return_value = mock_client

        wrapped = algorithm(
            name="test_algo",
            feasibility_function=sample_feasibility,
            scoring_function=sample_scoring,
            api_key="valid_key",
            is_minimization=True,
        )(sample_algorithm)

        assert wrapped(5) == 10
        assert wrapped(10) == 20
        assert wrapped(15) == 30

        assert mock_client.upload_instance.call_count == 3
        assert MockAPIClient.call_count == 1


def test_decorator_happy_path():
    with patch("algobench.decorator.APIClient") as MockAPIClient:
        mock_client = Mock()
        mock_client.login.return_value = True
        MockAPIClient.return_value = mock_client

        wrapped = algorithm(
            name="test_algo",
            feasibility_function=sample_feasibility,
            scoring_function=sample_scoring,
            api_key="valid_key",
            is_minimization=True,
        )(sample_algorithm)

        assert wrapped(5) == 10

        mock_client.upload_instance.assert_called_once()
        mock_client.upload_solution.assert_called_once()
