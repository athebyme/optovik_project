class CustomError(Exception):
    def __init__(self, error_type, message):
        super().__init__(message)
        self.error_type = error_type
        self.message = message

    def __str__(self):
        return f"{self.error_type}: {self.message}"