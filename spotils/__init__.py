"""Initialises the global instance & console and setups logging."""

import logging
from importlib.metadata import metadata

import dotenv
from rich.console import Console

from spotils.client import generate_global_instance
from spotils.helpers.logging import InterceptHandler

package_metadata = metadata(__package__)
__version__ = package_metadata["version"]
__app_name__ = package_metadata["name"]


dotenv.load_dotenv()
console = Console()
instance = generate_global_instance()

logging.basicConfig(
    handlers=[InterceptHandler()], level=logging.INFO, force=True
)
