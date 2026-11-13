from typing import Protocol, TypeVar

from code_compass.ports.io_objects import InputRequest

T = TypeVar("T", bound=InputRequest)


class InputPort(Protocol):

    def get_input(self, request: T) -> T:
        ...