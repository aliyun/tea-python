class Logger:
    levels = {
        'DEBUG': 10,
        'INFO': 20,
        'WARNING': 30,
        'ERROR': 40,
        'CRITICAL': 50
    }

    current_level = levels['DEBUG']
    log_format = "{levelname}: {message}"

    @staticmethod
    def log(level_name, message):
        if Logger.levels[level_name] >= Logger.current_level:
            print(Logger.log_format.format(levelname=level_name, message=message))

    @staticmethod
    def info(message):
        Logger.log('INFO', message)
    
    @staticmethod
    def debug(message):
        Logger.log('DEBUG', message)
    
    @staticmethod
    def warning(message):
        Logger.log('WARNING', message)
    
    @staticmethod
    def error(message):
        Logger.log('ERROR', message)
    
    @staticmethod
    def critical(message):
        Logger.log('CRITICAL', message)

    @staticmethod
    def set_level(level_name):
        if level_name in Logger.levels:
            Logger.current_level = Logger.levels[level_name]
        else:
            raise ValueError(f"Invalid log level: {level_name}")

    @staticmethod
    def format(log_format):
        Logger.log_format = log_format