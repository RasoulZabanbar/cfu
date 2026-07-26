"""
Seeds:
  - Permissions: full, basic
  - Roles: user, super_user   (super_user gets BOTH permissions)
  - One super_user account (bale_id=1484104109, phone=09012844143)

Run with:  python -m seed
(assumes Tortoise is already initialized elsewhere via your app's
TORTOISE_ORM config — see run_seed() below for a standalone runner)
"""

import asyncio

from tortoise import Tortoise, run_async

from models import User, Role, Permission
from boot.tortoise import TORTOISE_ORM
SUPER_USER_BALE_ID = 1484104109
SUPER_USER_PHONE = "09012844143"

PERMISSIONS = [
    {"code": "full", "label": "دسترسی کامل"},
    {"code": "basic", "label": "دسترسی پایه"},
]

ROLES = [
    {"name": "user", "is_system": True},
    {"name": "super_user", "is_system": True},
]


async def seed_permissions() -> dict[str, Permission]:
    permissions = {}
    for perm in PERMISSIONS:
        obj, _ = await Permission.get_or_create(
            code=perm["code"], defaults={"label": perm["label"]}
        )
        permissions[obj.code] = obj
    return permissions


async def seed_roles() -> dict[str, Role]:
    roles = {}
    for role in ROLES:
        obj, _ = await Role.get_or_create(
            name=role["name"], defaults={"is_system": role["is_system"]}
        )
        roles[obj.name] = obj
    return roles


async def assign_role_permissions(roles: dict[str, Role], permissions: dict[str, Permission]) -> None:
    super_user_role = roles["super_user"]
    # super_user gets full AND basic
    await super_user_role.permissions.add(permissions["full"], permissions["basic"])

    # plain "user" role only gets basic access by default
    user_role = roles["user"]
    await user_role.permissions.add(permissions["basic"])


async def seed_super_user(roles: dict[str, Role]) -> User:
    user, created = await User.get_or_create(
        bale_id=SUPER_USER_BALE_ID,
        defaults={
            "phone_number": SUPER_USER_PHONE,
            "full_name": "Super Admin",
        },
    )
    if not created and user.phone_number != SUPER_USER_PHONE:
        user.phone_number = SUPER_USER_PHONE
        await user.save()

    await user.roles.add(roles["super_user"])
    return user


async def seed() -> None:
    permissions = await seed_permissions()
    roles = await seed_roles()
    await assign_role_permissions(roles, permissions)
    await seed_super_user(roles)
    print("Seed complete: permissions=full,basic  roles=user,super_user  super_user assigned.")


async def run_seed_standalone() -> None:
    """Use this only if you don't already initialize Tortoise elsewhere."""
    await Tortoise.init(config=TORTOISE_ORM )
    await Tortoise.generate_schemas(safe=True)
    await seed()
    await Tortoise.close_connections()


if __name__ == "__main__":
    run_async(run_seed_standalone())