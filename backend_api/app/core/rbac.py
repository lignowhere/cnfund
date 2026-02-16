from typing import Iterable


READ_ROLES = {"viewer", "admin", "fund_manager"}
MUTATE_ROLES = {"admin", "fund_manager"}
ADMIN_ONLY_ROLES = {"admin"}


def has_role(user_role: str, allowed_roles: Iterable[str]) -> bool:
    return user_role in set(allowed_roles)

