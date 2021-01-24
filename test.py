from mcproto.server import Server


def log(event, *args):
    print(event)
    for arg in args:
        print('  ', repr(arg))


myserv = Server()
myserv.on('all', log)

myserv.listen()
