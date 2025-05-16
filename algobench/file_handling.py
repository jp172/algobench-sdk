import base64
import json
import pickle
import logging

logger = logging.getLogger(__name__)

def convert_to_string(object) -> tuple[str, str]:
        if hasattr(object, "model_dump_json"):
            return object.model_dump_json(), "json"
        elif hasattr(object, "to_json"):
            return json.dumps(object.to_json()), "json"
        logger.warning(f"No valid json or dict method found for {object}. Falling back to pickle.")
        return base64.b64encode(pickle.dumps(object)).decode('utf-8'), "pickle"

def convert_from_string(data, data_type, class_type: type) -> object:
    if data_type == "json":
        if hasattr(class_type, "model_validate_json"):
            return class_type.model_validate_json(data)
        elif hasattr(class_type, "from_json"):
            if isinstance(data, str):
                return class_type.from_json(data)
            else:
                return class_type.from_json(json.dumps(data))
        else:
            return json.loads(data)
    elif data_type == "pickle":
        return pickle.loads(base64.b64decode(data))
    else:
        raise ValueError(f"Invalid data type: {data_type}")