import logging
from functools import wraps

from .file_handling import convert_from_string
from .validation import validate, validate_input
from .api_client import APIClient

logger = logging.getLogger(__name__)


def algorithm(algorithm_function, name: str, feasibility_function: any, scoring_function: any, API_KEY: str, is_minimization: bool, improve_solution: bool = False):
    
    if not validate(algorithm_function, name, feasibility_function, scoring_function, API_KEY):
        logger.warning("Falling back to normal algorithm execution")
        return algorithm_function
    
    api_client = APIClient(API_KEY, name)
    if not api_client.login():
        logger.warning("API Key not valid. Falling back to normal algorithm execution")
        return algorithm_function
    
    api_client.upload_environment(algorithm_function, feasibility_function, scoring_function, is_minimization)

    def improve(instance, instance_id, solution):

        solution_string = api_client.pull_solution(instance_id)
        if solution_string is None:
            return solution
        try:
            server_solution = convert_from_string(solution_string[0], solution_string[1], type(solution))
        except Exception as e:
            logger.warning(f"Improving solution failed: {e}")
            return solution
        try:
            if feasibility_function(instance, server_solution):
                old_score = scoring_function(instance, solution)
                new_score = scoring_function(instance, server_solution)
                if is_minimization and old_score > new_score:
                    return server_solution
                elif not is_minimization and old_score < new_score:
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
            api_client.upload_solution(solution, instance_id)
        except Exception as e:
            logger.warning(f"Uploading solution failed: {e}")
        
        if improve_solution:
            try:
                return improve(instance, instance_id, solution)
            except Exception as e:
                logger.warning(f"Improving solution failed: {e}")

        return solution
    
    return wrapper
