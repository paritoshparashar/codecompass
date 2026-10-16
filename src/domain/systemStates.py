from enum import auto


class SystemState (Enum) :
    NOT_INITIALIZED = auto() # system is not initialized yet
    READY = auto() # system is ready to accept a new issue