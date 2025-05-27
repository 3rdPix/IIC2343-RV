"""Core module for the package. It holds the main object to be used."""
from typing import List, Optional, Callable
import serial
from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo
from enum import IntEnum
from dataclasses import dataclass

from iic2343.utils import (
    close_port,
    open_port,
    validate_port_selection,
    write_to_port,
)

__all__ = {"Basys3"}

PayloadBuilder = Callable[[int, bytearray], bytearray]

class Basys3:
    """
    Encapsulates the behaviour required for the data to be written to
    the Basys3 board.
    """

    class PortConfigurations:
        """@private"""
        BAUD_RATE = 115200
        BYTE_SIZE = 8
        STOP_BITS = 2
        XON_XOFF = 0
        RTS_CTS = 0

    class Default:
        """@private
        Preserved defaults to avoid breaking old proyects
        """
        BOTTOM_ADDRESS = 0
        TOP_ADDRESS = 2 ** 12
        WORD_LENGTH = 5

    @dataclass
    class Dims:
        BOTTOM_ADDRESS: int
        TOP_ADDRESS: int
        WORD_LENGTH: int

    def __init__(self, botAddrs: int=Default.BOTTOM_ADDRESS,
                 topAddrs: int=Default.TOP_ADDRESS,
                 wLen: int=Default.WORD_LENGTH) -> None:
        """
        Initialize Basys3 with specified settings
        -----------------------------------------------
        These defaults are set to preserve compatibility with old proyects.
        You should not change them unless you know what you are doing.

        If you do know what you are doing, consider adjusting the `wLen`
        to match the ROM width expected by the Basys3's **Programmer**. If you
        do; you will also need to pass a `Callable` reference in this class'
        `write` method that follows the protocol:

        >>> def custom_payload(addr: int, word: bytearray) -> bytearray: ...
        
        Where the returned value should be the **strict value** of the payload
        given to `serial.Serial`'s write method.

        If you need port-related custom speficications, you should *override*
        this class' `PortConfigurations` with your own settings before
        calling `__init__`. These constants are used to set up the port
        through the **Serial** lib.
        """
        self.__port = serial.Serial(
            baudrate=self.PortConfigurations.BAUD_RATE,
            bytesize=self.PortConfigurations.BYTE_SIZE,
            stopbits=self.PortConfigurations.STOP_BITS,
            xonxoff=self.PortConfigurations.XON_XOFF,
            rtscts=self.PortConfigurations.RTS_CTS)
        self.__dimensions = self.Dims(botAddrs, topAddrs, wLen)

    @property
    def bottom_address(self): return self.__dimensions.BOTTOM_ADDRESS

    @property
    def top_address(self): return self.__dimensions.TOP_ADDRESS

    @property
    def word_length(self): return self.__dimensions.WORD_LENGTH

    @property
    def available_ports(self) -> List[ListPortInfo]:
        """Get available ports."""
        return sorted(list_ports.comports())

    def begin(self, port_number: Optional[int] = None) -> None:
        """Configure and initialize the port to be used."""
        validate_port_selection(port_number, self.available_ports)
        self.__port.port = self.available_ports[port_number or 0].device
        open_port(self.__port)

    def end(self) -> None:
        """Close the port."""
        close_port(self.__port)

    def write(self, address: int, word: bytearray,
              custom_payload: PayloadBuilder=None) -> int:
        """Write to the initialized port."""
        if not self.can_be_written(address, word):
            return 0
        if custom_payload:
            return self.__port.write(custom_payload(self.__port, address, word))
        return write_to_port(self.__port, address, word)

    def can_be_written(self, address: int, word: bytearray) -> bool:
        """Checks if a word can be written on an address through a given port."""
        if not self.bottom_address <= address < self.top_address: return False
        if len(word) != self.word_length: return False
        if not self.__port.is_open: return False
        return True