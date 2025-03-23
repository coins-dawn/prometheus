from pydantic import BaseModel


def convert_for_json(obj):
    if isinstance(obj, BaseModel):
        return obj.dict()
    elif isinstance(obj, list):
        return [convert_for_json(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_for_json(v) for k, v in obj.items()}
    elif hasattr(obj, "__dataclass_fields__"):
        return {k: convert_for_json(getattr(obj, k)) for k in obj.__dataclass_fields__}
    else:
        return obj
