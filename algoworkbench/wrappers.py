import inspect
from functools import wraps

def upload_class_definition(item):
    print(f"uploading class {item}")
    print(f"Content: {inspect.getsource(item)}")

def upload_function(func_type, func):
    """
    Simulates uploading a function's metadata and source code.
    You can replace this with actual logic (e.g., HTTP request, database save).
    """
    func_metadata = {
        "type": func_type,
        "name": func.__name__,
        "source_code": inspect.getsource(func),
    }

    annotations = func.__annotations__
    print("Function annotations:", annotations)
    # Look for custom classes in the annotations
    for param, annotation in annotations.items():
        # Check if the annotation is a generic type, e.g., list[Item]
        if hasattr(annotation, "__origin__") and annotation.__origin__ is list:
            # Extract the type of the list elements (e.g., Item)
            item_type = annotation.__args__[0]
            if inspect.isclass(item_type):
                # Upload the class definition for the list element type
                upload_class_definition(item_type)

    func_module = inspect.getmodule(func)
    module_globals = func_module.__dict__
    # Scan function body for references to custom classes
    for name, obj in module_globals.items():
        if inspect.isclass(obj) and obj.__module__ == func_module.__name__:
            # Upload any custom classes defined in the module
            upload_class_definition(obj)

    print(f"Uploading {func_type} function '{func.__name__}'")
    print("Uploaded data:", func_metadata)

def upload_call_arguments(func_type, func_name, args, kwargs):
    """
    Uploads arguments of a function call (each time it's invoked).
    """
    call_metadata = {
        "type": func_type,
        "name": func_name,
        "args": args,
        "kwargs": kwargs,
    }
    print(f"Uploading arguments for {func_type} function '{func_name}'...")
    print("Uploaded call arguments:", call_metadata)

# Decorator registry to store marked functions
FUNCTION_REGISTRY = {
    'compute': None,
    'feasibility': None,
    'score': None,
}

# Decorator for marking compute functions
def compute(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Running compute function: {func.__name__}")
        result = func(*args, **kwargs)
        upload_call_arguments("compute", func.__name__, args, kwargs)
        print(f"Compute result: {result}")
        return result
    
    # Register the function
    FUNCTION_REGISTRY['compute'] = func
    upload_function("compute", func)
    return wrapper

# Decorator for marking feasibility functions
def feasibility(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Running feasibility function: {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Feasibility result: {'Feasible' if result else 'Not Feasible'}")
        return result
    
    # Register the function
    FUNCTION_REGISTRY['feasibility'] = func
    upload_function("feasibility", func)
    return wrapper

# Decorator for marking score functions
def score(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Running score function: {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Score result: {result}")
        return result
    
    # Register the function
    FUNCTION_REGISTRY['score'] = func
    upload_function("score", func)
    return wrapper
