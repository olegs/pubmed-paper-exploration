import configparser


class Config:
    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self.svd_dimensions = self._config.getint("clustering", "svd_dimensions")
        self.topic_words = self._config.getint("clustering", "topic_words")
        self.download_folder = self._config["ingestion"]["download_folder"]

config = Config("config.ini")