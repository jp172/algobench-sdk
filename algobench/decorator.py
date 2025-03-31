from dataclasses import dataclass
import inspect
import logging
import dill as pickle
from functools import wraps
import sys
import requests

logger = logging.getLogger(__name__)

@dataclass
class APIClient:
    api_key: str
    env_name: str
    algobench_url: str = "http://localhost:8000"
    environment_id: str | None = None

    def __post_init__(self):
        self.headers = {"Authorization": f"ApiKey {self.api_key}"}

    def check_api_key(self) -> bool:
        if not self.api_key:  # Check for empty API key
            return False
        response = requests.get(f"{self.algobench_url}/api/environments", headers=self.headers)
        return response.status_code == 200

    def get_environment(self) -> str | None:
        response = requests.get(f"{self.algobench_url}/api/environments", headers=self.headers)
        if response.status_code != 200:
            raise Exception("Failed to get environments")
        
        for environment in response.json():
            if environment["name"] == self.env_name:
                return environment["id"]
        return None

    def validate_input(self, args, kwargs):
        if len(args) != 1:
            raise Exception("Instance Upload failed. Algorithm must take exactly one argument")
        return args[0]
        
    def upload_instance(self, args, kwargs):
        instance = self.validate_input(args, kwargs)

        # TODO. conversion to/from json as fallback
        try:
            instance_json = instance.to_json()
        except (AttributeError, Exception) as e:
            instance_json = pickle.dumps(instance)

        response = requests.post(
            f"{self.algobench_url}/api/instances/", 
            json={"content": instance_json, "environment": self.environment_id},
            headers=self.headers
        )
        if response.status_code != 201:
            logger.warning(f"Instance Upload failed. {response.json()}")
            return None
        return response.json()["id"]
        

    def upload_result(self, result, instance_id):
        try:
            result_json = result.to_json()
        except Exception as e:
            result_json = pickle.dumps(result)
        
        # TODO. conversion to/from json as fallback
        response = requests.post(
            f"{self.algobench_url}/api/solutions/", 
            json={"content": result_json, "instance": instance_id},
            headers=self.headers
        )
        if response.status_code != 201:
            logger.warning(f"Result Upload failed. {response.json()}")
        else:
            result_id = response.json()["id"]
            return result_id

    def upload_environment(self, algorithm_function, feasibility, scoring):

        # TODO: Instance and Solution validation, ideally already during env upload.
        python_version = sys.version_info
        source_code = inspect.getsource(algorithm_function)

        algorithm_name = f"{algorithm_function.__module__}_{algorithm_function.__name__}"
        feasibility_name = f"{feasibility.__module__}_{feasibility.__name__}"
        scoring_name = f"{scoring.__module__}_{scoring.__name__}"

        json_data = {
            "python_version": python_version,
            "code": source_code,
            "algorithm_function_name": algorithm_name,
            "feasibility_function_name": feasibility_name,
            "score_function_name": scoring_name,
            "name": self.env_name,
        }

        environment = self.get_environment()
        if environment is not None:
            response = requests.put(
                f"{self.algobench_url}/api/environments/{environment}/", 
                json=json_data, 
                headers=self.headers
            )
            if response.status_code != 200:
                logger.warning(f"Environment Upload failed. {response.json()}")
        else:
            response = requests.post(
                f"{self.algobench_url}/api/environments/", 
                json=json_data, 
                headers=self.headers
            )
            if response.status_code != 201:
                logger.warning(f"Environment Upload failed. {response.json()}")
                logger.warning(f"Environment: {response.status_code}")
            else:
                self.environment_id = response.json()["id"]

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
    if inspect.signature(scoring_function).return_annotation is not float and inspect.signature(scoring_function).return_annotation is not int:
        logger.warning("scoring_function must return a float or int")
        return False

    return True


def validate(algorithm_function, name: str, feasibility_function: any, scoring_function: any, API_KEY: str) -> bool:
    if len(name) == 0:
        logger.warning("Environment name cannot be empty. Falling back to normal algorithm execution")
        return False
    
    if not (inspect.getsourcefile(algorithm_function) == inspect.getsourcefile(feasibility_function) == inspect.getsourcefile(scoring_function)):
        logger.warning("algorithm, feasibility, and scoring must be in the same file")
        return False
    
    if not validate_functions(algorithm_function, feasibility_function, scoring_function):
        return False
    
    return True

def algorithm(algorithm_function, name: str, feasibility_function: any, scoring_function: any, API_KEY: str):
    
    if not validate(algorithm_function, name, feasibility_function, scoring_function, API_KEY):
        logger.warning("Falling back to normal algorithm execution")
        return algorithm_function
    
    api_client = APIClient(API_KEY, name)
    if not api_client.check_api_key():
        logger.warning("API Key not valid. Falling back to normal algorithm execution")
        return algorithm_function
    
    api_client.upload_environment(algorithm_function, feasibility_function, scoring_function)

    @wraps(algorithm_function)
    def wrapper(*args, **kwargs):
        try:
            instance_id = api_client.upload_instance(args, kwargs)
        except Exception as e:
            logger.warning(f"Uploading instance failed: {e}")
            return algorithm_function(*args, **kwargs)
        
        result = algorithm_function(*args, **kwargs)
        
        try:
            api_client.upload_result(result, instance_id)
        except Exception as e:
            logger.warning(f"Uploading result failed: {e}")
        finally:
            return result
    
    return wrapper
