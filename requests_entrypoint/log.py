import logging
import os
import sys
import time

from estela_queue_adapter import queue_noisy_libraries
from requests_entrypoint.utils import producer

_stderr = sys.stderr


def to_standard_str(text, encoding="utf-8", errors="strict"):
    if isinstance(text, str):
        return text
    if not isinstance(text, bytes):
        raise TypeError("Unable to standardize {} type".format(type(text).__name__))
    return text.decode(encoding, errors)


def _logfn(level, message, parent="none"):
    data = {
        "jid": os.getenv("ESTELA_SPIDER_JOB"),
        "payload": {"log": str(message), "datetime": float(time.time())},
    }
    producer.send("job_logs", data)


def init_logging():
    # General python logging
    root = logging.getLogger()
    root.setLevel(
        logging.NOTSET
    )  # NOSET Make processing all messages if is set in root

    hdlr = LogHandler()
    hdlr.setLevel(logging.DEBUG)
    hdlr.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
    root.addHandler(hdlr)

    #Silence commonly used noisy libraries
    nh = logging.NullHandler()
    for ln in queue_noisy_libraries:
        lg = logging.getLogger(ln)
        lg.propagate = 0
        lg.addHandler(nh)
    # # Redirect standard output and error
    sys.stdout = StdoutLogger(False, "UTF-8")
    print("it should send to logs in kafka.")

    return hdlr


class LogHandler(logging.Handler):
    """Python logging handler"""

    def emit(self, record):
        try:
            message = self.format(record)
            if message:
                _logfn(message=message, level=record.levelno, parent="LogHandler")
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def handleError(self, record):
        cur = sys.stderr
        try:
            sys.stderr = _stderr
            super(LogHandler, self).handleError(record)
        finally:
            sys.stderr = cur


class StdoutLogger:
    """Catch logs from sterr and stdout"""

    def __init__(self, isError=False, encoding=None, loglevel=logging.INFO, fileno=None):
        self.prefix = "[stderr] " if isError else "[stdout] "
        self.loglevel = loglevel
        self.encoding = encoding
        self.buf = ""

    @staticmethod
    def fileno():
        return 1

    def _logprefixed(self, msg):
        _logfn(message=self.prefix + msg, level=self.loglevel, parent="StdoutLogger")

    def write(self, data):
        data = to_standard_str(data, self.encoding)

        d = (self.buf + data).split("\n")
        self.buf = d[-1]
        messages = d[0:-1]
        for message in messages:
            self._logprefixed(message)
            
    def flush(self):
        if self.buf:
            self.buf = ""

    def writelines(self, lines):
        for line in lines:
            line = to_standard_str(line, self.encoding)
            self._logprefixed(line)
