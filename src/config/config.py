import configparser

#############################
## Embeddings settings #####
#############################

# Size of a chunk for global text embeddings used for clustering
EMBEDDINGS_CHUNK_SIZE = 512
EMBEDDINGS_SENTENCE_OVERLAP = 0

# Size of a chunk for precise questioning
EMBEDDINGS_QUESTIONS_CHUNK_SIZE = 64
EMBEDDINGS_QUESTIONS_SENTENCE_OVERLAP = 1


#############################
## Embeddings settings #####
#############################

# Size of a chunk for global text embeddings used for clustering
EMBEDDINGS_CHUNK_SIZE = 512
EMBEDDINGS_SENTENCE_OVERLAP = 0

# Size of a chunk for precise questioning
EMBEDDINGS_QUESTIONS_CHUNK_SIZE = 64
EMBEDDINGS_QUESTIONS_SENTENCE_OVERLAP = 1

#####################
## Analysis config ##
#####################

# Global vectorization max vocabulary size
VECTOR_WORDS = 10_000

# Terms with lower frequency will be ignored, remove rare words
VECTOR_MIN_DF = 0.001

# Terms with higher frequency will be ignored, remove abundant words
VECTOR_MAX_DF = 0.8

#####################
## Word2vec config ##
#####################

WORD2VEC_EMBEDDINGS_LENGTH = 128
WORD2VEC_WINDOW = 5
WORD2VEC_EPOCHS = 3




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
        self.bern2_url = self._config["BERN2"]["url"]
        self.bern2_rate_limit = self._config.getint("BERN2", "rate_limit")

config = Config("config.ini")