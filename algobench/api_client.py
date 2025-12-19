import subprocess
import requests
import sys
import inspect
from dataclasses import dataclass
import logging
import os

from .file_handling import convert_to_json, convert_from_json


logger = logging.getLogger(__name__)


@dataclass
class APIClient:
    api_key: str
    env_name: str
    problem_id: str | None = None

    def __post_init__(self):
        self.headers = {"Authorization": f"ApiKey {self.api_key}"}
        self.algobench_url = os.getenv("ALGOBENCH_URL", "https://algobench.io")

    def login(self) -> bool:
        if not self.api_key:
            return False
        try:
            response = requests.get(f"{self.algobench_url}/api/problems?name={self.env_name}", headers=self.headers)
            if response.status_code != 200:
                logger.warning(f"Login failed. Status code: {response.status_code}. {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            logger.warning("Login failed. Could not connect to the server.")
            return False

        if len(response.json()) > 0:
            self.problem_id = response.json()[0]["id"]

        logger.info("Login successful.")
        return True

    def upload_instance(self, instance) -> str | None:
        response = requests.post(
            f"{self.algobench_url}/api/instances/",
            data={"content": convert_to_json(instance), "problem": self.problem_id},
            headers=self.headers,
        )

        if response.status_code != 201:
            logger.warning(f"Instance Upload failed. {response.text}")
            return None
        return response.json()["id"]

    def upload_solution(self, solution, instance_id: str, feasible: bool, score: float) -> str | None:
        response = requests.post(
            f"{self.algobench_url}/api/solutions/",
            data={"content": convert_to_json(solution), "instance": instance_id, "feasible": feasible, "score": score},
            headers=self.headers,
        )

        if response.status_code != 201:
            logger.warning(f"Solution Upload failed. {response.text}")
            return None

        return response.json()["id"]

    def upload_problem(self, algorithm_function, feasibility, scoring, is_minimization: bool):

        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        requirements = subprocess.check_output(["uv", "pip", "freeze"]).decode("utf-8")

        file_path = inspect.getfile(algorithm_function)
        with open(file_path, "r") as f:
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
        }

        if self.problem_id is not None:
            response = requests.put(
                f"{self.algobench_url}/api/problems/{self.problem_id}/", json=json_data, headers=self.headers
            )
            if response.status_code != 200:
                logger.warning(f"Problem upload failed.  {response.text}")
        else:
            response = requests.post(f"{self.algobench_url}/api/problems/", json=json_data, headers=self.headers)
            if response.status_code != 201:
                logger.warning(f"Problem upload failed. {response.text}")
                logger.warning(f"Problem: {response.status_code}")
            else:
                self.problem_id = response.json()["id"]
                logger.info("Problem uploaded successfully.")

    def pull_solution(self, instance_id: str, solution_type: type) -> object | None:
        response = requests.get(
            f"{self.algobench_url}/api/instances/{instance_id}/best_solution/", headers=self.headers
        )

        if response.status_code == 404:
            logger.info(f"No solution found for instance {instance_id}")
            return None
        elif response.status_code != 200:
            logger.warning(f"Solution Pull failed. Status code: {response.status_code}. {response.text}")
            return None

        data = response.json()

        if len(data) == 0:
            logger.info(f"No solution found for instance {instance_id}")
            return None

        if "content" not in data:
            logger.warning(f"Solution Pull failed. Data: {data}")
            return None

        return convert_from_json(data["content"], solution_type)
