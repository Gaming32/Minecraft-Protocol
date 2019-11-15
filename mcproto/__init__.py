"""Version numbers are \"<mcproto version>/<minecraft protocol version>\""""
from .common import protocol_version
from .client import Client, ping
from .server import Server
__all__ = ['Client', 'Server', 'protocol_version', 'ping']
__version__ = '0.2b/'
__version__ += str(protocol_version)