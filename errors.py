class UserErrors:

    class UserNotFound(Exception):

        def __init__(self, message: str):
            self.message = message

            super().__init__(self.message)

        def __str__(self):
            return f'{self.message}'

    class ExistingUser(Exception):

        def __init__(self, message: str):
            self.message = message

            super().__init__(self.message)

        def __str__(self):
            return f'{self.message}'

    class InvalidDictForm(Exception):

        def __init__(self, message: str):
            self.message = message

            super().__init__(self.message)

        def __str__(self):
            return f'{self.message}'


class EmbedErrors:

    class InvalidNeighborType(Exception):

        def __init__(self, message: str):
            self.message = message

            super().__init__(self.message)

        def __str__(self):
            return f'{self.message}'
