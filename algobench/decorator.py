import logging
from functools import wraps
import time

from .validation import validate, validate_input
from .api_client import APIClient

logger = logging.getLogger(__name__)


def algorithm(
    name: str,
    feasibility_function: any,
    scoring_function: any,
    api_key: str,
    is_minimization: bool,
    additional_wait_seconds: int = 0,
):

    def create_decorator(algorithm_function):
        if not validate(algorithm_function, name, feasibility_function, scoring_function, api_key):
            logger.warning("Falling back to normal algorithm execution")
            return algorithm_function

        api_client = APIClient(api_key, name)
        if not api_client.login():
            logger.warning("Falling back to normal algorithm execution")
            return algorithm_function

        api_client.upload_problem(algorithm_function, feasibility_function, scoring_function, is_minimization)

        def improve(instance, instance_id, solution, old_solution_feasible, old_score):

            server_solution = api_client.pull_solution(instance_id, type(solution))
            if server_solution is None:
                return solution
            try:
                if feasibility_function(instance, server_solution):
                    new_score = scoring_function(instance, server_solution)
                    if (
                        (is_minimization and old_score > new_score)
                        or (not is_minimization and old_score < new_score)
                        or not old_solution_feasible
                    ):
                        logger.info(f"Improved solution found. New score: {new_score}. Old score: {old_score}")
                        return server_solution
                    else:
                        return solution
            except Exception as e:
                logger.warning(f"Improving solution failed: {e}")
                return solution

        @wraps(algorithm_function)
        def wrapper(*args, **kwargs):

            try:
                instance = validate_input(args, kwargs)
                instance_id = api_client.upload_instance(instance)
            except Exception as e:
                logger.warning(f"Uploading instance failed: {e}")
                return algorithm_function(*args, **kwargs)

            solution = algorithm_function(*args, **kwargs)

            try:
                feasible = feasibility_function(instance, solution)
                score = scoring_function(instance, solution)
                api_client.upload_solution(solution, instance_id, feasible, score)
            except Exception as e:
                logger.warning(f"Uploading solution failed: {e}")

            time.sleep(additional_wait_seconds)
            try:
                return improve(instance, instance_id, solution, feasible, score)
            except Exception as e:
                logger.warning(f"Improving solution failed: {e}")

            return solution

        return wrapper

    return create_decorator
