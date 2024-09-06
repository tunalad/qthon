# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=broad-exception-caught
# pylint: disable=multiple-imports


import os
import toml
from appdirs import user_config_dir


class Config:
    def __init__(self, config_path=None):
        if config_path is None or not os.path.exists(config_path):
            config_path = os.path.join(user_config_dir(), "qthon", "config.toml")
            if not os.path.exists(config_path):
                self.make_config(config_path)

        super().__init__()

        self.config_path = config_path
        self.parsed_cfg = self.load_config(config_path)

    def print_config(self):
        __import__("pprint").pprint(self.parsed_cfg)

    def load_config(self, path):
        with open(path, "r") as f:
            return toml.load(f)

    def update_config(self, new_settings):
        with open(self.config_path, "w") as f:
            toml.dump(new_settings, f)

    def make_config(self, path):
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
