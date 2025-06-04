import logging
from path_manager import LOGS_DIR
import sys


class Custom_Logger(logging.Logger):
    def critical(self, msg, *args, **kwargs):
        """
        Terminate python run if critical error occured.

        :parameter
            msg: the log message
        """
        super().critical(msg, *args, **kwargs)
        sys.exit(-1)


logging.basicConfig(filename=LOGS_DIR,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

logging.setLoggerClass(Custom_Logger)

logger = logging.getLogger(__name__)

