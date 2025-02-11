from enum import Enum
import inspect
import logging
import dill as  pickle
import subprocess
import os
from functools import partial, wraps
import sys

from .dependency_finding import _get_local_files

ALGO_WORKBENCH_ENDPOINT = "https://algoworkbench.com/upload"

# TODO can this just be a variable?
class NoOp:
    active = False

no_op = NoOp()

class Uploader:

    def __init__(self, prefix="../awb-backend/examples"):
        self.path_prefix = prefix

    def upload_python_object(self, path_suffix, object, file_name):
        full_path = self.path_prefix + f"/{path_suffix}/{file_name}"
        path = os.path.dirname(full_path)
        file_name = os.path.basename(path)
        
        os.makedirs(path, exist_ok=True)
        with open(full_path, "wb") as f:
            logging.info(f"Uploading {file_name}, {object}")
            if isinstance(object, str):
                f.write(object.encode())
            else:
                f.write(pickle.dumps(object))

    def upload_file(self, path_suffix, file_path):
        ROOT_DIR = os.path.abspath(os.curdir)

        file_name = os.path.basename(file_path)
        folder_path = os.path.dirname(file_path)
        source_path =  os.path.join(ROOT_DIR, file_path)

        target_path = f"{self.path_prefix}/{path_suffix}/{folder_path}"
        os.makedirs(target_path, exist_ok=True)

        with open(f"{target_path}/{file_name}", "w") as target:
            with open(source_path, "r") as source:
                target.write(source.read())

uploader = Uploader()


def upload_input(func_name, args, kwargs):
    uploader.upload_python_object(func_name, args, "args.pkl")
    uploader.upload_python_object(func_name, kwargs, "kwargs.pkl")

def upload_result(func_name, result):
    uploader.upload_python_object(func_name, result, "solution.pkl")

def upload_function(func, file_path, file_name):
    try:
        source_code = inspect.getsource(func)
        if "<locals>" in func.__qualname__:
            raise ValueError("Callable must be defined at the module level.")
        func_name = f"{func.__module__}:{func.__qualname__}"
        logging.info(source_code)
        uploader.upload_python_object(file_path, source_code, file_name)
    except Exception as e:
        logging.warning(f"Could not upload function {func}: {e}")

def _upload_entire_env(func):
    python_version = sys.version_info
    uploader.upload_python_object("env", f"{python_version.major}.{python_version.minor}", "python_version.txt")

    try:
        requirements = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    except Exception as e:
        requirements = "# Could not run pip freeze\n"
    uploader.upload_python_object("env", requirements, "requirements.txt")

    for path in _get_local_files(func):
        uploader.upload_file("env", path)


class WrapperType(Enum):
    COMPUTE = "compute"
    SCORE = "score"
    FEASIBILITY = "feasibility"
    

def generic_wrapper(func, type: WrapperType, project: str="default", upload_args: bool=True, upload_results: bool=True, upload_env: str=False):
    count = 0
    @wraps(func)
    def wrapper(*args, **kwargs):
        name = project + f"/{type.value}"
        nonlocal count
        print(f"{func} no op: {no_op.active}")
        if count == 0 and not no_op.active:
            if not getattr(wrapper, f"_uploaded_env", False) and upload_env:
                _upload_entire_env(func)
                setattr(wrapper, f"_uploaded_env", True)

            if not getattr(wrapper, f"_uploaded_func_{name}", False):
                upload_function(func, project, f"{type.value}.py")
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

def create_decorator(wrapper_type, upload_env=False):
    def decorator(func=None, **kwargs):
        if func is None:
            return lambda f: generic_wrapper(f, type=wrapper_type, upload_env=upload_env, **kwargs)
        return generic_wrapper(func, type=wrapper_type, upload_env=upload_env)
    return decorator


compute = create_decorator(WrapperType.COMPUTE, upload_env=True)
feasibility = create_decorator(WrapperType.FEASIBILITY)
score = create_decorator(WrapperType.SCORE)