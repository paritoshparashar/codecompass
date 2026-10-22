from enum import Enum, auto


class SystemState (Enum) :
    NOT_INITIALIZED = auto() # system is not initialized yet
    INITIALIZED = auto() # system is ready to accept a new issue