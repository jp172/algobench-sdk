import inspect
import pickle
import random
import subprocess
import os
from functools import partial, wraps
import sys

from .dependency_finding import _get_local_files

ALGO_WORKBENCH_ENDPOINT = "https://algoworkbench.com/upload"

# PLAN
# 2. Server-side: Store the uploaded data
# 3. Server-side: Replicate function run.
#   - Fetch all instances, copy into docker container, run, feasibility check, score, copy results back.
# 4. Server-side: Create new functions and run it.

# Essential features
# * mapping of input and output args from compute to input args of feasibility and score.
# * do a smart evaluation of new functions. Compute on small instances first, or instances that fail often (or where many fcts score low?)
# to save on compute.

# --> feature: detect corner cases that the function doesn't handle well.
# --> load test the function on a variety of instances.
# --> feature: detect if the function is slow on some instances.


class Uploader:

    def __init__(self, root="upload"):
        self.path = root
        pass


    def upload_python_object(self, func_name, object, file_name):
        # create directory if it doesn't exist
        os.makedirs(self.path + f"/{func_name}", exist_ok=True)
        with open(self.path + f"/{func_name}/{file_name}", "wb") as f:
            print(func_name, file_name, object)
            if isinstance(object, str):
                f.write(object.encode())
            else:
                f.write(pickle.dumps(object))

    def upload_file(self, func_name, file_path):
        file_name = os.path.basename(file_path)
        # create directory if it doesn't exist
        print(func_name, file_path)
        os.makedirs(self.path + f"/{func_name}", exist_ok=True)
        with open(self.path + f"/{func_name}/{file_name}", "w") as f:
            with open(file_path, "r") as f2:
                f.write(f2.read())


uploader = Uploader()


def upload_input(func_name, args, kwargs):
    uploader.upload_python_object(func_name, args, "args")
    uploader.upload_python_object(func_name, kwargs, "kwargs")

def upload_result(func_name, result):
    uploader.upload_python_object(func_name, result, "result")

def upload_function(func_name, func, uploaded_file_name):
    try:
        source_code = inspect.getsource(func)
        uploader.upload_python_object(func_name, source_code, uploaded_file_name)
    except Exception as e:
        print("Could not upload function:", e)

def _upload_entire_env(func, func_name):
    python_version = sys.version_info
    uploader.upload_python_object("env", f"{python_version.major}.{python_version.minor}", "python_version.txt")

    try:
        requirements = subprocess.check_output(["pip", "freeze"], text=True)
    except Exception as e:
        requirements = "# Could not run pip freeze\n"
    uploader.upload_python_object("env", requirements, "requirements.txt")

    for path in _get_local_files(func):
        uploader.upload_file("env", path)


def generic_wrapper(func, name: str, upload_args: bool=True, upload_results: bool=True, upload_env: str=False):
    count = 0
    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal count
        count += 1
        func_name = name + "_{}".format(count)
        if upload_args:
            upload_input(func_name, args, kwargs)
        result = func(*args, **kwargs)
        if upload_results:
            upload_result(func_name, result)
        return result
    
    if not getattr(wrapper, f"_uploaded_env", False) and upload_env:
        _upload_entire_env(func, name)
        setattr(wrapper, f"_uploaded_env", True)

    if not getattr(wrapper, f"_uploaded_func_{name}", False):
        upload_function("wrapped_fcts", func, f"{name}.py")
        setattr(wrapper, f"_uploaded_func_{name}", True)
    
    return wrapper


compute = partial(generic_wrapper, name="compute", upload_env=True)
feasibility = partial(generic_wrapper, name="feasibility")
score = partial(generic_wrapper, name="score")