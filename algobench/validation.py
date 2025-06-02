import logging
import inspect

logger = logging.getLogger(__name__)


def validate_functions(algorithm_function, feasibility_function, scoring_function):
    hints = list(inspect.signature(algorithm_function).parameters.values())

    if len(hints) != 1:
        logger.warning("algorithm_function must take exactly one argument")
        return False
    potential_instance_type = hints[0].annotation
    potential_solution_type = inspect.signature(algorithm_function).return_annotation
    feasibility_hints = list(inspect.signature(feasibility_function).parameters.values())
    if len(feasibility_hints) != 2:
        logger.warning("feasibility_function must take exactly two arguments")
        return False
    if feasibility_hints[0].annotation != potential_instance_type:
        logger.warning("feasibility_function must take the same instance type as algorithm_function")
        return False
    if feasibility_hints[1].annotation != potential_solution_type:
        logger.warning("feasibility_function must take the same solution type as algorithm_function")
        return False
    if inspect.signature(feasibility_function).return_annotation is not bool:
        logger.warning("feasibility_function must return a boolean")
        return False

    scoring_hints = list(inspect.signature(scoring_function).parameters.values())
    if len(scoring_hints) != 2:
        logger.warning("scoring_function must take exactly two arguments")
        return False
    if scoring_hints[0].annotation != potential_instance_type:
        logger.warning("scoring_function must take the same instance type as algorithm_function")
        return False
    if scoring_hints[1].annotation != potential_solution_type:
        logger.warning("scoring_function must take the same solution type as algorithm_function")
        return False
    if (
        inspect.signature(scoring_function).return_annotation is not float
        and inspect.signature(scoring_function).return_annotation is not int
    ):
        logger.warning("scoring_function must return a float or int")
        return False

    return True


def validate(algorithm_function, name: str, feasibility_function: any, scoring_function: any, API_KEY: str) -> bool:
    if len(name) == 0:
        logger.warning("Problem name cannot be empty. Falling back to normal algorithm execution")
        return False

    if not (
        inspect.getsourcefile(algorithm_function)
        == inspect.getsourcefile(feasibility_function)
        == inspect.getsourcefile(scoring_function)
    ):
        logger.warning("algorithm, feasibility, and scoring must be in the same file")
        return False

    if not validate_functions(algorithm_function, feasibility_function, scoring_function):
        return False

    return True


def validate_input(args, kwargs):
    if len(args) + len(kwargs) != 1:
        raise Exception("Validation failed. Algorithm must take exactly one argument")
    if len(args) == 1:
        return args[0]
    if len(kwargs) == 1:
        return list(kwargs.values())[0]
    raise Exception("Validation failed. Algorithm must take exactly one argument")
