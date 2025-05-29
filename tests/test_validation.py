from unittest.mock import patch
from algobench.validation import validate_functions, validate


def sample_algorithm(x: int) -> int:
    return x * 2


def sample_feasibility(x: int, y: int) -> bool:
    return True


def sample_scoring(x: int, y: int) -> float:
    return x


def test_different_source_files():
    with patch("inspect.getsourcefile") as mock_getsourcefile:
        # Mock different source files for each function
        mock_getsourcefile.side_effect = lambda func: {
            sample_algorithm: "file1.py",
            sample_feasibility: "file1.py",
            sample_scoring: "file2.py",
        }[func]

        # Should fail because functions are from different files
        assert not validate(sample_algorithm, "name", sample_feasibility, sample_scoring, "api_key")

    with patch("inspect.getsourcefile") as mock_getsourcefile:
        # Mock same source file for all functions
        mock_getsourcefile.return_value = "same_file.py"

        # Should pass because all functions are from the same file
        assert validate(sample_algorithm, "name", sample_feasibility, sample_scoring, "api_key")


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
