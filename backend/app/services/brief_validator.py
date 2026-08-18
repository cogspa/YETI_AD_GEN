"""Brief validation service using CampaignBriefModel."""

import json
from typing import Dict, Any, Tuple, List, Optional
from pydantic import ValidationError
from backend.app.models.brief import CampaignBriefModel


def validate_brief_dict(data: Dict[str, Any]) -> Tuple[bool, Optional[CampaignBriefModel], List[str]]:
    """
    Validate a brief dictionary against the strict CampaignBriefModel contract.
    Returns:
        (is_valid, validated_model_or_none, error_messages_list)
    """
    try:
        model = CampaignBriefModel.model_validate(data)
        return True, model, []
    except ValidationError as e:
        errors = []
        for err in e.errors():
            loc = " -> ".join(str(p) for p in err["loc"])
            msg = err["msg"]
            errors.append(f"[{loc}] {msg}")
        return False, None, errors
    except Exception as ex:
        return False, None, [f"Unexpected error validating brief: {str(ex)}"]


def validate_brief_json_file(file_path: str) -> Tuple[bool, Optional[CampaignBriefModel], List[str]]:
    """Validate a JSON file path."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return validate_brief_dict(data)
    except json.JSONDecodeError as jde:
        return False, None, [f"Invalid JSON file format: {jde.msg} at line {jde.lineno}, col {jde.colno}"]
    except Exception as ex:
        return False, None, [f"Failed to read file {file_path}: {str(ex)}"]
