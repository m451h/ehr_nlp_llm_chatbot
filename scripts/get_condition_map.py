import sys
sys.path.insert(0, '.')

from typing import Dict


def get_condition_name_to_id() -> Dict[str, str]:
    # Lazy import to avoid loading FastAPI app context
    from api import get_available_conditions

    id_to_name = get_available_conditions()  # {id: name}
    name_to_id: Dict[str, str] = {name: cid for cid, name in id_to_name.items()}
    return name_to_id


if __name__ == "__main__":
    import json
    mapping = get_condition_name_to_id()
    print(json.dumps(mapping, ensure_ascii=False, indent=2))


