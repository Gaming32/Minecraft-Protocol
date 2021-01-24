from typing import Any, Callable
from .common import *


class Connection:
    address: tuple[str, int]
    connection: socket.socket

    def __init__(self, conn, addr) -> None:
        self.address = addr
        self.connection = conn

    def __repr__(self) -> str:
        return f'<{self.address}: {self.connection}>'


class Server:
    _events: dict[str, list[Callable[..., None]]]
    _singular_event_defaults: dict[str, Callable[..., Any]]
    _singular_events: dict[str, Callable[..., Any]]
    connections: dict[tuple[str, int], Connection]

    protocol_version: int

    def __init__(self, protocol_version: int = PROTOCOL_VERSION):
        self._events = {}
        self._singular_event_defaults = {
            'status': self._default_status
        }
        self._singular_events = self._singular_event_defaults.copy()
        self.connections = {}
        self.protocol_version = protocol_version

    def _default_status(self, conn: Connection, *args):
        return {}

    def _invoke_singular_event(self, evname, *args, **kwargs):
        return self._singular_events[evname](*args, **kwargs)

    def _invoke_event(self, evname, *args, **kwargs):
        evobj_list = self._events.get(evname)
        if evobj_list is not None:
            for evobj in evobj_list:
                evobj(*args, **kwargs)
        evobj_list = self._events.get('all')
        if evobj_list is not None:
            for evobj in evobj_list:
                evobj(evname, *args, **kwargs)
    
    def _handshake(self, conn: socket.socket):
        id, data = get_packet(conn.recv(8192))
        if id != 0x00:
            return None
        stream = io.BytesIO(data)
        proto = read_var_int(stream)
        local_addr = read_string(stream)
        local_port = int.from_bytes(stream.read(2), 'big', signed=False)
        next_state = read_var_int(stream)
        return (proto, local_addr, local_port, next_state)

    def _send_status(self, conn: Connection, handshake):
        get_packet_safe(conn.connection)
        result = self._invoke_singular_event('status', conn, *handshake[:-1])
        json_data = json.dumps(result)
        stream = io.BytesIO()
        write_string(stream, json_data)
        conn.connection.send(make_packet(0x00, stream.getvalue()))
        try:
            packid, pack = get_packet_safe(conn.connection)
        except ConnectionError:
            pass
        else:
            number = int.from_bytes(pack, 'big', signed=True)
            stream = io.BytesIO()
            stream.write(number.to_bytes(8, 'big', signed=True))
            conn.connection.send(make_packet(0x01, stream.getvalue()))

    def on(self, event, *callbacks):
        if event in self._singular_events:
            if not callbacks:
                self._singular_events[event] = self._singular_event_defaults[event]
            elif len(callbacks) > 1:
                raise ValueError(f'only one callback is supported for the event {event!r}')
            else:
                self._singular_events[event] = callbacks[0]
        self._events.setdefault(event, [])
        if not callbacks:
            self._events[event].clear()
        else:
            self._events[event].extend(callbacks)

    def listen(self, host='::', port=25565, backlog=None):
        sock = socket.create_server((host, port), family=socket.AF_INET6, backlog=backlog, dualstack_ipv6=True)
        while True:
            conn, addr = sock.accept()
            new_connection = Connection(conn, addr)
            self.connections[addr] = new_connection
            self._invoke_event('connect', new_connection)
            handshake_result = self._handshake(conn)
            if handshake_result is None:
                self._invoke_event('disallowed', new_connection, 'first packet not 0x00')
                continue
            self._invoke_event('handshake', conn, *handshake_result)
            if handshake_result[-1] == 1:
                self._send_status(new_connection, handshake_result)
