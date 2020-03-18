# -*- coding:utf-8 -*-
import select
import socketserver as sse
import socket
from copy import deepcopy
import bz2
import threading as t
import ChatServer


class ChatServerAsync(ChatServer.ChatServer):
    def __init__(self, port, file_transmission_port, max_file_size=8192, radio_broadcast_address="192.168.1.255",
                 server_name="TestChat"):
        super(ChatServerAsync, self).__init__(port=port, log_file_route=None, max_file_size=max_file_size,
                                              address=radio_broadcast_address, server_name=server_name)
        if not self.server_name:
            self.server_name = "TestChat"
        if not self.address:
            self.address = "192.168.1.255"
        self.sock = socket.socket()
        self.sock.bind(("0.0.0.0", port))
        self.sock.listen(125)
        self.sock_map = {self.sock.fileno(): self.sock}

    def processing_connections(self):
        t.Thread(target=self.file_send).start()
        t.Thread(target=self.processing_communication).start()
        poll = select.poll()
        poll.register(self.sock)
        while True:
            events = poll.poll()
            if events:
                for sock_obj, event in events:
                    if sock_obj == self.sock.fileno():
                        client, address = self.sock.accept()
                        print("EVENT: New connect:" + address[0])
                        poll.register(client.fileno(), select.POLLIN)
                        self.sock_map[client.fileno()] = client
                        break
                    elif event is select.POLLIN:
                        data = self.sock_map[sock_obj].recv(1024000)
                        if not data:
                            print(self.sock_map[sock_obj].getsockname()[0] + "Closed")
                            poll.unregister(sock_obj)
                            del self.sock_map[sock_obj]
                            break
                        data = bz2.decompress(data).decode("UTF-32")
                        data2 = data.split("-!seq!-")
                        data = data2[0] + "(%s)\n" % self.sock_map[sock_obj].getsockname()[0]
                        self._lock.acquire()
                        self.new_message = deepcopy(data)
                        self._lock.release()
                    else:
                        print("Unknown event:" + str(event))

    def processing_communication(self, socket_="Not support", name1="Not support"):
        while True:
            if self.new_message != self.old_message:
                for x in self.sock_map:
                    for x2 in range(8):
                        try:
                            self.sock_map[x].send(bz2.compress(self.new_message.encode("utf-32") + "-!seq!-".encode("utf-32")))
                        except BrokenPipeError:
                            pass
                self.old_message = deepcopy(self.new_message)

    def start_server(self):
        t.Thread(target=self.radio_broadcast).start()
        self.processing_connections()


def main():
    max_fz = int(input("Please enter the max file size(enter for 8MB):") or 8192000)
    sn = input("Please enter the server name(enter for TestChat):" or None)
    broadcast = input("Please enter the radio broadcast address(enter for 192.168.1.255):" or None)
    chat = ChatServerAsync(8505, 8506, max_fz, broadcast, sn)
    chat.start_server()


if __name__ == '__main__':
    main()
