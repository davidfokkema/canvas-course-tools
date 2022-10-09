import pathlib

import appdirs
import toml


APP_NAME = "canvas-course-tools"
CONFIG_FILE = "config.toml"


def read_config():
    """Read configuration file."""
    config_path = get_config_path()
    if config_path.is_file():
        with open(config_path) as f:
            return toml.load(f)
    else:
        return {}


def write_config(config):
    """Write configuration file.

    Args:
        config: a dictionary containing the configuration.
    """
    create_config_dir()
    config_path = get_config_path()
    toml_config = toml.dumps(config)
    with open(config_path, "w") as f:
        # separate TOML generation from writing to file, or an exception
        # generating TOML will result in an empty file
        f.write(toml_config)


def get_config_path():
    """Get path of configuration file."""
    config_dir = pathlib.Path(appdirs.user_config_dir(APP_NAME))
    config_path = config_dir / CONFIG_FILE
    return config_path


def create_config_dir():
    """Create configuration directory if necessary."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
