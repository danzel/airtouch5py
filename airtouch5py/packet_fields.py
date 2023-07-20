from enum import Enum


class MessageType(Enum):
    # Control command and status message
    CONTROL_STATUS = 0xC0
    EXTENDED = 0x1F


class ControlStatusSubType(Enum):
    ZONE_CONTROL = 0x20
    ZONE_STATUS = 0x21
    AC_CONTROL = 0x22
    AC_STATUS = 0x23


class ExtendedMessageSubType(Enum):
    AC_ABILITY = 0xFF11
    AC_ERROR_INFORMATION = 0xFF10
    ZONE_NAME = 0xFF13
    CONSOLE_VERSION = 0xFF30
