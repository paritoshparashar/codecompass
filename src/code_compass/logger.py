

class Logger :

    depth = 1

    @staticmethod
    def log_start(string: str):
        Logger.print_start_separator(Logger)
        print(string)
        Logger.print_empty_line()

    @staticmethod
    def log_end(string: str):
        print(string)
        Logger.print_end_separator(Logger)

    def print_start_separator(self):
        print("-" * (100/Logger.depth).__int__())
        Logger.increment_depth(Logger)

    def print_end_separator(self):
        Logger.decrement_depth(Logger)
        print("-" * (100/Logger.depth).__int__())

    @staticmethod
    def print_empty_line():
        print("\n")

    def increment_depth(self):
        Logger.depth += 1

    def decrement_depth(self):
        if Logger.depth > 1:
            Logger.depth -= 1