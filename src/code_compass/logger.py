class Logger:
    depth = 1
    _RED = "\033[31m"
    _GREEN = "\033[32m"
    _RESET = "\033[0m"

    @staticmethod
    def log_start(string: str):
        Logger._print_start_separator(Logger)
        print(string)
        Logger.print_empty_line()

    @staticmethod
    def log_end(string: str):
        Logger.print_empty_line()
        print(string)
        Logger._print_end_separator(Logger)

    @staticmethod
    def log(string: str):
        print(string)

    @staticmethod
    def red(string: str) -> str:
        return f"{Logger._RED}{string}{Logger._RESET}"

    @staticmethod
    def green(string: str) -> str:
        return f"{Logger._GREEN}{string}{Logger._RESET}"

    @staticmethod
    def print_empty_line():
        print("\n")

    def _print_start_separator(self):
        print("-" * (100 / Logger.depth).__int__())
        Logger._increment_depth(Logger)

    def _print_end_separator(self):
        Logger._decrement_depth(Logger)
        print("-" * (100 / Logger.depth).__int__())

    def _increment_depth(self):
        Logger.depth += 1

    def _decrement_depth(self):
        if Logger.depth > 1:
            Logger.depth -= 1
