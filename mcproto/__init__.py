"""Version numbers are \"<mcproto version>/<minecraft protocol version>\""""
from .common import PROTOCOL_VERSION
from .client import ping
from .server import Server
__all__ = ['Client', 'Server', 'protocol_version', 'ping']
__version__ = '0.2b/'
__version__ += str(PROTOCOL_VERSION)
