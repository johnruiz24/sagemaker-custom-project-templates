import json
import uuid
from datetime import datetime


class Logger:
    log_levels = None

    def __init__(self, correlation_id=None):
        self.correlation_id = correlation_id

    def set_correlation_id(self, correlation_id):
        self.correlation_id = correlation_id

    def debug(self, message, correlation_id=None):
        if self.correlation_id:
            return self.log("DEBUG", message, self.correlation_id)
        elif correlation_id:
            return self.log("DEBUG", message, correlation_id)
        else:
            return self.log("DEBUG", message)

    def info(self, message, correlation_id=None):
        if self.correlation_id:
            return self.log("INFO", message, self.correlation_id)
        elif correlation_id:
            return self.log("INFO", message, correlation_id)
        else:
            return self.log("INFO", message)

    def warn(self, message, correlation_id=None):
        if self.correlation_id:
            return self.log("WARN", message, self.correlation_id)
        elif correlation_id:
            return self.log("WARN", message, correlation_id)
        else:
            return self.log("WARN", message)

    def error(self, message, correlation_id=None):
        if self.correlation_id:
            return self.log("ERROR", message, self.correlation_id)
        elif correlation_id:
            return self.log("ERROR", message, correlation_id)
        else:
            return self.log("ERROR", message)

    def critical(self, message, correlation_id=None):
        if self.correlation_id:
            return self.log("CRITICAL", message, self.correlation_id)
        elif correlation_id:
            return self.log("CRITICAL", message, correlation_id)
        else:
            return self.log("CRITICAL", message)

    @staticmethod
    def log(severity, message, correlation_id=None):
        """
        Logs an event to stdout in a json conform way for the central
        monitoring environment using the following JSON:

        { d
            "CorrelationID": (uuid),
            "Timestamp": (ISO-8601 compliant timestamp in UTC),
            "System": "Search",
            "Severity": (described below),
            "Message": (The message to log)
        }

        args:
            severity(str): This is either one of DEBUG, INFO, WARN, ERROR,
            CRITICAL
            message(str): Log message that will be added to the event
            correlation_id(uuid): Usually the context has a uuid already
            present if this is passed as `None` it will generate a new uuid
        """
        if not correlation_id:
            correlation_id = uuid.uuid4()
        log_event = {
            "CorrelationID": str(correlation_id),
            "Timestamp": datetime.utcnow().isoformat(),
            "System": "brain-api-services",
            "Severity": severity,
            "Message": message
        }
        print(json.dumps(log_event), flush=True)
        # this is mainly for the unittesting but can technically also be used
        # to act on this log event - though I can't see any use in that right
        # now
        return log_event
