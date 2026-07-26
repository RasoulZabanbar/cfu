from boot.config import get_env_setup

_env_setup = get_env_setup()


TORTOISE_ORM = {
    "connections": {"default": _env_setup.database_url},
    "apps": {
        "models": {
            "models": ["models.user"],
            "default_connection": "default",
            "migrations": "models.migrations",
        },
    },
}