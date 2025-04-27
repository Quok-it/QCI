import datetime

class Logger:
    def log(self, message: str) -> None:
        print(f"[{datetime.datetime.now()}] {message}")

    def log_error(self, error: Exception, context: str = "") -> None:
        print(f"[{datetime.datetime.now()}] ERROR in {context}: {str(error)}")
