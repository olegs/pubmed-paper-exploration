import configparser


class Config:
    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self.svd_dimensions = self._config.getint("clustering", "svd_dimensions")
        self.topic_words = self._config.getint("clustering", "topic_words")
        if self.topic_words < 5:
            raise ValueError("clustering.topic_words must be greater than or equal to 5. Please check the configuration.")
        self.download_folder = self._config["ingestion"]["download_folder"]
        self.loglevel = self._config["logging"]["log_level"]
        self.angel_config = {
            "model_load_path": self._config["ANGEL"]["model_load_path"],
            "model_token_path": self._config["ANGEL"]["model_token_path"],
            "per_device_eval_batch_size": self._config.getint("ANGEL", "per_device_eval_batch_size"),
            "num_beams": self._config.getint("ANGEL", "num_beams"),
            "prefix_mention_is": self._config.getboolean("ANGEL", "prefix_mention_is"),
        }

config = Config("config.ini")