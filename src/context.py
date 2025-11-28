from utils.config import configs_map
from utils.validators import validators_map
from utils.processors import processors_map
from utils.database import database_map


class AppContext:
    def __init__(self):
        self.configs_map = configs_map
        self.validators_map = validators_map
        self.processors_map = processors_map
        self.database_map = database_map
