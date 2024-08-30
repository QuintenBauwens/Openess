import logging

# custom log level
THREAD_LEVEL_NUM = 5
logging.addLevelName(THREAD_LEVEL_NUM, "THREAD")

def thread(self, message, *args, **kws):
	if self.isEnabledFor(THREAD_LEVEL_NUM):
		self._log(THREAD_LEVEL_NUM, message, args, **kws)
		
logging.Logger.thread = thread

FILE_NAME = "AppLog.log"
LOG_LEVEL = "INFO"
# LOG_LEVEL = logging.Logger.thread
LOG_FORMAT = "%(asctime)s - %(filename)s  %(levelname)s  %(message)s"
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"

class CustomFormatter(logging.Formatter):
	def format(self, record):
		file_name = record.filename.split('.')[0]
		# pad the filename to 20 characters
		record.filename = f"{file_name:<15}"
		# Pad the log level to 8 characters
		record.levelname = f"{record.levelname:<8}"
		return super().format(record)


def update_logger_config(settings):
	global FILE_NAME, LOG_LEVEL

	# Update log level
	logger_level = settings.get('logger_level', LOG_LEVEL)[0]
	log_level_mapping = {
		'(lowest) THREAD': THREAD_LEVEL_NUM,
		'DEBUG': logging.DEBUG,
		'INFO': logging.INFO,
		'WARNING': logging.WARNING,
		'ERROR': logging.ERROR,
		'(highest) CRITICAL': logging.CRITICAL
	}
	log_level_setting = log_level_mapping.get(logger_level, logging.INFO)

	# update the log level for all loggers
	for name in logging.root.manager.loggerDict:
		logger = logging.getLogger(name)
		logger.setLevel(log_level_setting)
	

	# Update log file name
	file_name_setting = settings.get('logger_file', FILE_NAME)[0]

	if not file_name_setting.endswith('.log'):
		raise ValueError("Log file name must end with '.log' extension, defaulting to 'AppLog.log'")
	if file_name_setting != FILE_NAME:
		FILE_NAME = file_name_setting
		# Reconfigure handlers for all loggers
		for name in logging.root.manager.loggerDict:
			print(name)
			logger = logging.getLogger(name)
			if logger.hasHandlers():
				print('has handlers')
				for handler in logger.handlers:
					print(handler)
					if isinstance(handler, logging.FileHandler):
						print('closing handler')
						handler.close()
						logger.removeHandler(handler)
				file_handler = logging.FileHandler(FILE_NAME, mode='a')
				file_handler.setFormatter(CustomFormatter(LOG_FORMAT, datefmt=DATE_FORMAT))
				logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
	logger = logging.getLogger(name)
	# logger.setLevel(THREAD_LEVEL_NUM) # set the logger level to the custom level so that it can log the custom level
	logger.setLevel(getattr(logging, LOG_LEVEL)) 

	if not logger.hasHandlers():
		# makes sure that the logger is not already configured
		# create log file, when maxBytes is reached, the file is renamed and a new file is created
		file_handler = logging.FileHandler(FILE_NAME, mode='a')
		file_handler.setFormatter(CustomFormatter(LOG_FORMAT, datefmt=DATE_FORMAT))
		logger.addHandler(file_handler)

		console_handler = logging.StreamHandler()
		console_handler.setFormatter(CustomFormatter(LOG_FORMAT, datefmt=DATE_FORMAT))
		logger.addHandler(console_handler)
	return logger