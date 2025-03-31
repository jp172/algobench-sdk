import pytest
from algobench.decorator import APIClient, algorithm, validate_functions
from unittest.mock import Mock, patch

def sample_algorithm(x: int) -> int:
    return x * 2

def sample_feasibility(x: int, y: int) -> bool:
    return True

def sample_scoring(x: int, y: int) -> float:
    return x


def test_decorator_with_module_functions():
    with patch('algobench.decorator.APIClient') as MockAPIClient:
        mock_client = Mock()
        mock_client.check_api_key.return_value = True
        mock_client.upload_instance.return_value = "test_instance_id"
        MockAPIClient.return_value = mock_client

        wrapped = algorithm(
            sample_algorithm,
            name="test_algo",
            feasibility_function=sample_feasibility,
            scoring_function=sample_scoring,
            API_KEY="valid_key"
        )
        
        assert wrapped(5) == 10

def test_decorator_invalid_api_key():
    with patch('algobench.decorator.APIClient') as MockAPIClient:
        mock_client = Mock()
        mock_client.check_api_key.return_value = False
        MockAPIClient.return_value = mock_client

        wrapped = algorithm(
            sample_algorithm,
            name="test_algo",
            feasibility_function=sample_feasibility,
            scoring_function=sample_scoring,
            API_KEY="invalid_key"
        )
        
        assert wrapped == sample_algorithm

def test_decorator_empty_name():
    wrapped = algorithm(
        sample_algorithm,
        name="",
        feasibility_function=sample_feasibility,
        scoring_function=sample_scoring,
        API_KEY="valid_key"
    )
    
    assert wrapped == sample_algorithm

def test_decorator_different_source_files():
    with patch('algobench.decorator.APIClient') as MockAPIClient:
        mock_client = Mock()
        mock_client.check_api_key.return_value = True
        MockAPIClient.return_value = mock_client

        with patch('inspect.getsourcefile') as mock_getsourcefile:
            def mock_source_file(func):
                if func == sample_algorithm:
                    return "file1.py"
                elif func == sample_feasibility:
                    return "file2.py"
                else:
                    return "file2.py"
        
            mock_getsourcefile.side_effect = mock_source_file

            wrapped = algorithm(
                sample_algorithm,
                name="test_algo",
                feasibility_function=sample_feasibility,
                scoring_function=sample_scoring,
                API_KEY="valid_key"
            )
            
            assert wrapped == sample_algorithm

def test_decorator_upload_failures():
    with patch('algobench.decorator.APIClient') as MockAPIClient:
        mock_client = Mock()
        mock_client.check_api_key.return_value = True
        mock_client.upload_instance.side_effect = Exception("Upload failed")
        MockAPIClient.return_value = mock_client

        wrapped = algorithm(
            sample_algorithm,
            name="test_algo",
            feasibility_function=sample_feasibility,
            scoring_function=sample_scoring,
            API_KEY="valid_key"
        )
        
        assert wrapped(5) == 10
        mock_client.upload_instance.assert_called_once()





def test_decorator_persistence():
    with patch('algobench.decorator.APIClient') as MockAPIClient:
        mock_client = Mock()
        mock_client.check_api_key.return_value = True
        mock_client.upload_instance.return_value = "test_instance_id"
        MockAPIClient.return_value = mock_client

        wrapped = algorithm(
            sample_algorithm,
            name="test_algo",
            feasibility_function=sample_feasibility,
            scoring_function=sample_scoring,
            API_KEY="valid_key"
        )
        
        wrapped(5)
        wrapped(10)
        wrapped(15)
        
        assert mock_client.upload_instance.call_count == 3
        assert MockAPIClient.call_count == 1

def test_decorator_happy_path():
    with patch('algobench.decorator.APIClient') as MockAPIClient:
        mock_client = Mock()
        mock_client.check_api_key.return_value = True
        MockAPIClient.return_value = mock_client
        
        wrapped = algorithm(
            sample_algorithm,
            name="test_algo",
            feasibility_function=sample_feasibility,
            scoring_function=sample_scoring,
            API_KEY="valid_key"
        )
        
        assert wrapped(5) == 10
        
        mock_client.upload_instance.assert_called_once()
        mock_client.upload_result.assert_called_once()


class TestInstance:
    value: float = 0
        
class TestSolution:
    value: float = 0

def valid_feasibility(input: TestInstance, solution: TestSolution) -> bool:
    return True

def invalid_feasibility(input: TestInstance, solution: TestSolution) -> str:
    return "not a bool"

def valid_scoring(input: TestInstance, solution: TestSolution) -> float:
    return solution.value

def invalid_scoring(input: TestInstance, solution) -> int:
    return 0

def valid_function(input: TestInstance) -> TestSolution:
    return TestSolution(input.value * 2)

def invalid_function(input: TestInstance) -> str:
        return "not a TestSolution"

def test_function_validation():
    
    assert validate_functions(valid_function, valid_feasibility, valid_scoring)

    assert not validate_functions(valid_function, invalid_feasibility, valid_scoring)
    assert not validate_functions(valid_function, invalid_feasibility, invalid_scoring)
    assert not validate_functions(valid_function, valid_feasibility, invalid_scoring)

    assert not validate_functions(invalid_function, invalid_feasibility, invalid_scoring)
    assert not validate_functions(invalid_function, invalid_feasibility, valid_scoring)
    assert not validate_functions(invalid_function, valid_feasibility, valid_scoring)
    assert not validate_functions(invalid_function, valid_feasibility, invalid_scoring)