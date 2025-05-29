import json
import logging
from json.decoder import JSONDecodeError

logger = logging.getLogger(__name__)


def convert_to_json(object) -> str:
    if hasattr(object, "model_dump_json"):
        return object.model_dump_json()
    elif hasattr(object, "to_json"):
        return json.dumps(object.to_json())
    else:
        try:
            return json.dumps(object)
        except JSONDecodeError as e:
            logger.warning(f"No valid json or dict method found for {object}.")
            raise e


def convert_from_json(data, class_type: type) -> object:
    if hasattr(class_type, "model_validate_json"):
        if isinstance(data, str):
            return class_type.model_validate_json(data)
        else:
            return class_type.model_validate(data)
    elif hasattr(class_type, "from_json"):
        if isinstance(data, str):
            return class_type.from_json(data)
        else:
            return class_type.from_json(json.dumps(data))
    else:
        return json.loads(data)
