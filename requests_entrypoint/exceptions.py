class ProjectStructureException(Exception):
    """Exception raised for project structure issues."""

    def __init__(self, message):
        self.original_message = message
        full_message = f"Project structure exception: {self.original_message}"
        super().__init__(full_message)
