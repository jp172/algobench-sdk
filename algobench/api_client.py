import subprocess
import requests
import sys
import inspect
from dataclasses import dataclass
import logging

from .file_handling import convert_to_json, convert_from_json


logger = logging.getLogger(__name__)

@dataclass
class APIClient:
    api_key: str
    env_name: str
    algobench_url: str = "http://localhost:8000"
    environment_id: str | None = None

    def __post_init__(self):
        self.headers = {"Authorization": f"ApiKey {self.api_key}"}

    def login(self) -> bool:
        if not self.api_key:
            return False
        response = requests.get(f"{self.algobench_url}/api/environments?name={self.env_name}", headers=self.headers)
        if response.status_code != 200:
            return False
        
        if len(response.json()) > 0:
            self.environment_id = response.json()[0]["id"]
        return True
        
        
    def upload_instance(self, instance) -> str | None:
        response = requests.post(
            f"{self.algobench_url}/api/instances/", 
            data={"content": convert_to_json(instance), "environment": self.environment_id},
            headers=self.headers
        )
        
        if response.status_code != 201:
            logger.warning(f"Instance Upload failed. {response.json()}")
            return None
        return response.json()["id"]
        

    def upload_solution(self, solution, instance_id: str) -> str | None:
        response = requests.post(
            f"{self.algobench_url}/api/solutions/", 
            data={"content": convert_to_json(solution), "instance": instance_id},
            headers=self.headers
        )
        
        if response.status_code != 201:
            logger.warning(f"Solution Upload failed. {response.json()}")
            return None
        
        return response.json()["id"]

    def upload_environment(self, algorithm_function, feasibility, scoring, is_minimization: bool, improve_solution: bool):

        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        requirements = subprocess.check_output(["python", "-m", "pip", "freeze"]).decode("utf-8")

        file_path = inspect.getfile(algorithm_function)
        with open(file_path, 'r') as f:
            source_code = f.read()

        algorithm_name = f"{algorithm_function.__name__}"
        feasibility_name = f"{feasibility.__name__}"
        scoring_name = f"{scoring.__name__}"

        json_data = {
            "python_version": python_version,
            "requirements": requirements,
            "code": source_code,
            "algorithm_function_name": algorithm_name,
            "feasibility_function_name": feasibility_name,
            "score_function_name": scoring_name,
            "is_minimization": is_minimization,
            "name": self.env_name,
            "active": improve_solution
        }

        if self.environment_id is not None:
            response = requests.put(
                f"{self.algobench_url}/api/environments/{self.environment_id}/", 
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
                logger.info(f"Environment uploaded successfully.")
    
    def pull_solution(self, instance_id: str, solution_type: type) -> object | None:
        response = requests.get(
            f"{self.algobench_url}/api/instances/{instance_id}/best_solution/",
            headers=self.headers
        )
        
        if response.status_code != 200:
            logger.warning(f"Solution Pull failed. Status code: {response.status_code}. {response.json()}")
            return None
        
        data = response.json()
        
        if len(data) == 0:
            logger.warning(f"No solution found for instance {instance_id}")
            return None
        
        if "content" not in data:
            logger.warning(f"Solution Pull failed. Data: {data}")
            return None
        
        return convert_from_json(data["content"], solution_type)