from .common import *

def _handshake(host, port, protocol_version, state):
    sockobj = socket.socket()
    sockobj.connect((host, port))
    stream = io.BytesIO()
    write_var_int(stream, protocol_version)
    write_string(stream, host)
    stream.write(port.to_bytes(2, 'big', signed=False))
    write_var_int(stream, 1)
    sockobj.send(make_packet(0x00, stream.getvalue()))
    return sockobj

class Client:
    def __init__(self, username, password=None):
        if password is not None:
            self.user = authserver.authenticate_user(username, password)
            self.access_token = self.user['accessToken']
            self.profile = self.user['selectedProfile']
        else:
            self.user = None
            self.access_token = None
            self.profile = None
            raise NotImplementedError
    def connect(host='localhost', port=25565, protocol_version=protocol_version):
        pass

def ping(host='localhost', port=25565, protocol_version=protocol_version):
    sockobj = _handshake(host, port, protocol_version, 1)
    sockobj.send(make_packet(0x00))
    packet_id, data = get_packet(sockobj.recv(4096))
    if packet_id == 0x00:
        string = read_string(io.BytesIO(data)) + '}'
        json_data = json.loads(string)
    return json_data