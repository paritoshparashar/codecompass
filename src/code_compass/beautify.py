

class Beautify :

    depth = 1

    @staticmethod
    def log_start(string: str):
        Beautify.print_start_separator()
        print(string)
        Beautify.print_empty_line()

    @staticmethod
    def log_end(string: str):
        print(string)
        Beautify.print_end_separator()

    @staticmethod
    def print_start_separator():
        print("-" * (100/Beautify.depth).__int__())
        Beautify.increment_depth(Beautify)

    @staticmethod
    def print_end_separator():
        Beautify.decrement_depth(Beautify)
        print("-" * (100/Beautify.depth).__int__())

    @staticmethod
    def print_empty_line():
        print("\n")

    def increment_depth(self):
        Beautify.depth += 1

    def decrement_depth(self):
        if Beautify.depth > 1:
            Beautify.depth -= 1