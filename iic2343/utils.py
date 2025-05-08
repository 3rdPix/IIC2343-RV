"""Module to hold every utility of the library."""
from typing import List, Optional
import serial
from serial.tools.list_ports_common import ListPortInfo
from iic2343.errors import CannotOpenPortError, InvalidPortError, NoPortsPresentError


def open_port(port: serial.Serial) -> None:
    """Handles the opening of a port."""
    port.open()
    if port.is_open:
        port.write([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
    else:
        raise CannotOpenPortError("Cannot open requested serial port.")


def close_port(port: serial.Serial) -> None:
    """Handles the closing of a port."""
    port.write([0xFF])
    port.close()


def validate_port_selection(
    port_number: Optional[int], os_ports: List[ListPortInfo]
) -> None:
    """
    Checks if a port number is valid for an array of available ports.
    If the port number is invalid, raises an error.
    """
    if not os_ports:
        raise NoPortsPresentError("No serial ports present.")
    if len(os_ports) > 1 and port_number is None:
        raise InvalidPortError(
            f"{len(os_ports)} serial ports present, please select one."
        )
    if port_number is not None and not -1 < port_number < len(os_ports):
        raise InvalidPortError(
            f"Invalid port number '{port_number}', {len(os_ports)} serial "
            "ports present, please select a valid one."
        )

def write_to_port(port: serial.Serial, address: int, word: bytearray) -> int:
    """
    Writes some data into an address through a port, it assumes that the
    data can be written.
    """
    add = (address << 4).to_bytes(2, "big")
    payload = bytearray(
        [
            0xAA,
            0xAA,
            add[0],
            add[1] | (word[0] & 0xF),
            word[1],
            word[2],
            word[3],
            word[4],
            0xAA,
        ]
    )
    return port.write(payload)
