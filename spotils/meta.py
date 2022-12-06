"""Holds certain application metadata."""

from importlib.metadata import metadata

import platformdirs

package_metadata = metadata(__package__)
__version__ = package_metadata["version"]
__app_name__ = package_metadata["name"]

APPLICATION_PATHS = platformdirs.PlatformDirs(__app_name__, appauthor=False)
