import socket, io, json
from mojang_api.servers import authserver
protocol_version = 498

client_packet_type_names = []
client_packet_type_info = {}

def _read_var_int(stream:io.RawIOBase, maxsize):
    num_read = 0
    result = 0
    while True:
        read = stream.read(1)[0]
        value = read & 0b01111111
        result |= value << (7 * num_read)

        num_read += 1
        if num_read > maxsize:
            raise ValueError('VarInt/VarLong is too big')

        if not (read & 0b10000000):
            break

    return result

def read_var_int(stream:io.RawIOBase):
    return _read_var_int(stream, 5)

def read_var_long(stream:io.RawIOBase):
    return _read_var_int(stream, 10)

def _rshift_sign(val, n): return (val % 0x100000000) >> n

def write_var_int(stream:io.RawIOBase, value):
    while True:
        temp = value & 0b01111111
        value = _rshift_sign(value, 7)
        if value != 0:
            temp |= 0b10000000
        stream.write(bytes((temp,)))
        if not value:
            break

def get_packet(data):
    stream = io.BytesIO(data)
    length = read_var_int(stream)
    packet_id = read_var_int(stream)
    length -= stream.tell()
    return packet_id, stream.read(length)

def make_packet(packet_id, data=b''):
    stream_data = io.BytesIO()
    write_var_int(stream_data, packet_id)
    stream_data.write(data)
    length = stream_data.getbuffer().nbytes
    stream_length = io.BytesIO()
    write_var_int(stream_length, length)
    return stream_length.getvalue() + stream_data.getvalue()

def write_string(stream:io.RawIOBase, string):
    string = string.encode('utf-8')
    write_var_int(stream, len(string))
    stream.write(string)

def read_string(stream:io.RawIOBase):
    length = read_var_int(stream)
    string = stream.read(length)
    return string.decode('utf-8')