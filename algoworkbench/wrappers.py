import inspect
import logging
import dill as  pickle
import subprocess
import os
from functools import partial, wraps
import sys

from .dependency_finding import _get_local_files

ALGO_WORKBENCH_ENDPOINT = "https://algoworkbench.com/upload"

class NoOp:
    active = False

no_op = NoOp()

# PROTOTYPE
# 3. Server-side: Replicate function run: Fetch one instances, set up poetry, run, feasibility check, score, copy results back.
# instance_id, algorithm_id, solution, feasibility, score -> DB
# 4. Server-side: Generate new functions

# Essential features
# * mapping of input and output args from compute to input args of feasibility and score.
# * do a smart evaluation of new functions. Compute on small instances first, or instances that fail often (or where many fcts score low?)
# to save on compute.

# --> feature: detect corner cases that the function upload doesn't handle well.
# --> load test the function on a variety of instances.
# --> feature: detect if the function is slow on some instances.

class Uploader:

    def __init__(self, prefix="upload"):
        self.path_prefix = prefix

    def upload_python_object(self, func_name, object, file_name):
        # create directory if it doesn't exist
        path = self.path_prefix + f"/{func_name}"
        file = f"{path}/{file_name}"
        
        os.makedirs(path, exist_ok=True)
        with open(file, "wb") as f:
            logging.info(f"Uploading {func_name}, {file_name}, {object}")
            if isinstance(object, str):
                f.write(object.encode())
            else:
                f.write(pickle.dumps(object))

    def upload_file(self, file_path):
        ROOT_DIR = os.path.abspath(os.curdir)

        file_name = os.path.basename(file_path)
        folder_path = os.path.dirname(file_path)

        source_path =  os.path.join(ROOT_DIR, file_path)

        target_path = f"{self.path_prefix}/env/{folder_path}"
        os.makedirs(target_path, exist_ok=True)

        with open(f"{target_path}/{file_name}", "w") as target:
            with open(source_path, "r") as source:
                target.write(source.read())

uploader = Uploader()


def upload_input(func_name, args, kwargs):
    uploader.upload_python_object(func_name, args, "args")
    uploader.upload_python_object(func_name, kwargs, "kwargs")

def upload_result(func_name, result):
    uploader.upload_python_object(func_name, result, "result")

def upload_function(func, uploaded_file_name):
    try:
        source_code = inspect.getsource(func)
        if "<locals>" in func.__qualname__:
            raise ValueError("Callable must be defined at the module level.")
        func_name = f"{func.__module__}:{func.__qualname__}"
        uploader.upload_python_object("Function", source_code, uploaded_file_name)
    except Exception as e:
        logging.warning(f"Could not upload function {func_name}:", e)

def _upload_entire_env(func):
    python_version = sys.version_info
    uploader.upload_python_object("env", f"{python_version.major}.{python_version.minor}", "python_version.txt")

    try:
        requirements = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    except Exception as e:
        requirements = "# Could not run pip freeze\n"
    uploader.upload_python_object("env", requirements, "requirements.txt")

    for path in _get_local_files(func):
        uploader.upload_file(path)


def generic_wrapper(func, name: str, upload_args: bool=True, upload_results: bool=True, upload_env: str=False):
    count = 0
    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal count
        print(f"{func} no op: {no_op.active}")
        if count == 0 and not no_op.active:
            if not getattr(wrapper, f"_uploaded_env", False) and upload_env:
                _upload_entire_env(func)
                setattr(wrapper, f"_uploaded_env", True)

            if not getattr(wrapper, f"_uploaded_func_{name}", False):
                upload_function(func, f"{name}.py")
                setattr(wrapper, f"_uploaded_func_{name}", True)

        count += 1
        func_name = name + "_{}".format(count)
        if upload_args and not no_op.active:
            upload_input(func_name, args, kwargs)
        result = func(*args, **kwargs)
        if upload_results and not no_op.active:
            upload_result(func_name, result)
        return result
    
    return wrapper


compute = partial(generic_wrapper, name="compute", upload_env=True)
feasibility = partial(generic_wrapper, name="feasibility")
score = partial(generic_wrapper, name="score")