class Logger:
    _depth = 1
    _alpha = 0.25
    _increment_factor = 1 * _alpha
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

    @staticmethod
    def log_service_start(serviceName: str):
        Logger.log_start(f"{serviceName} Service: Started")

    @staticmethod
    def log_service_end(serviceName: str, withError: bool) -> None:
        if withError:
            Logger.log_end(
                f" {serviceName} Service: {Logger.red('Exited with Error')}"
            )
        else:
            Logger.log_end(
                f" {serviceName} Service: {Logger.green('Exited Successfully')}"
            )

    @staticmethod
    def log_success(str: None = None):
        if str is not None:
            Logger.log(f"{str}")
        Logger.log(f"{Logger.green('Success')}\n")

    @staticmethod
    def log_error(error: Exception):
        Logger.log(f"{Logger.red('Error')}: {error}")

    @staticmethod
    def log_failed(error: Exception):
        Logger.log_error(error)
        Logger.log(f"{Logger.red('Failed')}")

    def _print_start_separator(self):
        print("-" * (100 / Logger._depth).__int__())
        Logger._increment_depth(Logger)

    def _print_end_separator(self):
        Logger._decrement_depth(Logger)
        print("-" * (100 / Logger._depth).__int__())

    def _increment_depth(self):
        Logger._depth += Logger._increment_factor

    def _decrement_depth(self):
        if Logger._depth > 1:
            Logger._depth -= Logger._increment_factor
