class Issue:
    """Structure modeling a single issue."""

    def __init__(self, number: int, title: str, body: str = ""):
        self.number = number
        self.title = title
        self.body = body

    def combined_text(self):
        return self.title + " " + self.body

    def get_data(self):
        return [self.number, self.title, self.body]
