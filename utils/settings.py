# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=broad-exception-caught
# pylint: disable=multiple-imports


import os
import toml
from appdirs import user_config_dir


class Config:
    """
    Handles application configuration management using TOML format.
    """

    def __init__(self, config_path=None):
        """
        Initializes configuration, creating default config if none exists.

        Args:
            config_path (str, optional): Path to config file. If None, uses default user config directory.
        """
        if config_path is None or not os.path.exists(config_path):
            config_path = os.path.join(user_config_dir(), "qthon", "config.toml")
            if not os.path.exists(config_path):
                self.make_config(config_path)

        super().__init__()

        self.config_path = config_path
        self.parsed_cfg = self.load_config(config_path)

    def print_config(self):
        """Prints current configuration settings for debugging."""
        __import__("pprint").pprint(self.parsed_cfg)

    def load_config(self, path):
        """
        Loads configuration from TOML file.

        Args:
            path (str): Path to configuration file.

        Returns:
            dict: Parsed configuration settings.
        """
        with open(path, "r") as f:
            return toml.load(f)

    def update_config(self, new_settings):
        """
        Saves updated configuration to file.

        Args:
            new_settings (dict): New configuration settings to save.
        """
        with open(self.config_path, "w") as f:
            toml.dump(new_settings, f)

    def make_config(self, path):
        """
        Creates default configuration file.

        Args:
            path (str): Path where configuration file should be created.
        """
        defaults = {
            "default_zoom": 128,
            "water_port": 9742,
            "undo_limit": 0,
            "hide_item": {
                "sidebar": False,
                "statusbar": False,
                "toolbar": False,
            },
            "move_item": {"sidebar": False, "toolbar": False},
        }

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            toml.dump(defaults, f)


if __name__ == "__main__":
    cfg = Config("./config.toml")
    print(cfg.parsed_cfg["default_zoom"])
