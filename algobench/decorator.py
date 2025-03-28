from dataclasses import dataclass
import inspect
import logging
import dill as pickle
from functools import wraps
import sys

import requests

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
            logging.warning(f"Instance Upload failed. {response.json()}")
            return None
        return response.json()["id"]
        

    def upload_result(self, result, instance_id):
        try:
            result_json = result.to_json()
        except Exception as e:
            result_json = pickle.dumps(result)
        
        response = requests.post(
            f"{self.algobench_url}/api/solutions/", 
            json={"content": result_json, "instance": instance_id},
            headers=self.headers
        )
        if response.status_code != 201:
            logging.warning(f"Result Upload failed. {response.json()}")
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
                logging.warning(f"Environment Upload failed. {response.json()}")
        else:
            response = requests.post(
                f"{self.algobench_url}/api/environments/", 
                json=json_data, 
                headers=self.headers
            )
            if response.status_code != 201:
                logging.warning(f"Environment Upload failed. {response.json()}")
                logging.warning(f"Environment: {response.status_code}")
            else:
                self.environment_id = response.json()["id"]

def algorithm(algorithm_function, name: str, feasibility_function: any, scoring_function: any, API_KEY: str):
    
    if len(name) == 0:
        logging.warning("Environment name cannot be empty. Falling back to normal algorithm execution")
        return algorithm_function
    
    api_client = APIClient(API_KEY, name)
    if not api_client.check_api_key():
        logging.warning("API Key not valid. Falling back to normal algorithm execution")
        return algorithm_function
    
    # algorithm, feasibility, scoring must be in the same file for now
    if not (inspect.getsourcefile(algorithm_function) == inspect.getsourcefile(feasibility_function) == inspect.getsourcefile(scoring_function)):
        logging.warning("algorithm, feasibility, and scoring must be in the same file")
        return algorithm_function
    
    api_client.upload_environment(algorithm_function, feasibility_function, scoring_function)

    @wraps(algorithm_function)
    def wrapper(*args, **kwargs):
        try:
            instance_id = api_client.upload_instance(args, kwargs)
        except Exception as e:
            logging.warning(f"Uploading instance failed: {e}")
            return algorithm_function(*args, **kwargs)
        
        result = algorithm_function(*args, **kwargs)
        
        try:
            api_client.upload_result(result, instance_id)
        except Exception as e:
            logging.warning(f"Uploading result failed: {e}")
        finally:
            return result
    
    return wrapper
