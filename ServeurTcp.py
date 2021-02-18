from socket import socket, AF_INET, SOCK_STREAM, timeout
from threading import Thread
import json
from notifier import Notifier

DEBUG = False

class SyntheseRobot:
    OP = "Robot_OP"
    HS = "Robot_HS"

class ErrorLevels:
    OK = "OK"
    ERROR = "ERROR"

class ErrorMessages:
    CLOSED = "Connection_closed"
    LOST = "Connection_lost"
    ABORTED = "Connection_aborted" #Pas utiliser pour l'instant à voir l'utilité

class Server(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind(("", 888))
        self.socket.settimeout(0.5)
        self.running = False
        self.client_pool = []
        self.getConfig()
        self.notifier = Notifier()

    def getConfig(self):
        with open('./config.json') as json_file:
            config = json.load(json_file)
            self.tokens = config["Tokens"]
            self.translate = config["Translate"]
            self.robots = config["Ip_Robot"]
            self.robots_language = config["Robot_Language"]
            self.clients = config["Robot_PhoneNumber"]

    def stop(self):
        print("Server shutdown...")
        if self.client_pool :
            for client in self.client_pool:
                client.close_connection()
        self.running = False

    def sendNotification(self, robotAdresse, msg):
        self.getConfig()
        sn = self.robots[robotAdresse]
        language = self.robots_language[sn]
        if language not in self.translate["Supported Language"]:
            language = "en"
        clients = []
        if sn in self.clients:
            clients = self.clients[sn]
            
        self.notifier.sendNotifications(msg, clients, self.tokens, sn, self.translate, language)

    def client_handling_stopped(self, client, error_level, error_msg):
        if error_msg in [SyntheseRobot.HS,ErrorMessages.CLOSED,ErrorMessages.LOST]:
            self.sendNotification(client.address[0],error_msg)
        self.client_pool = [client for client in self.client_pool if client.alive]

    def run(self):
        print("Server start...")
        self.running = True
        self.socket.listen(5)
        while self.running:
            try:
                client, address = self.socket.accept()
            except timeout:
                continue
            if DEBUG:
                print(f"[{address[0]}] connected")
            client_handling = ClientHandling(client, address, self.client_handling_stopped)
            client_handling.start()
            self.client_pool.append(client_handling)


class ClientHandling(Thread):

    def __init__(self, client, address, exit_callback):
        Thread.__init__(self)
        self.client = client
        self.address = address
        self.exit_callback = exit_callback
        self.alive = True
        self.client.settimeout(2)

    def _stop(self, error_level: ErrorLevels, error_msg: ErrorMessages):
        self.alive = False
        self.close_connection()
        self.exit_callback(self, error_level, error_msg)

    def close_connection(self):
        self.alive = False
        self.client.close()
        if DEBUG:
            print(f"[{self.address[0]}] disconnected")

    def onMessage(self, message):
        if message == SyntheseRobot.HS:
            self._stop(ErrorLevels.OK, SyntheseRobot.HS)
            
    def run(self):
        try:
            response = self.client.recv(1024)
            while response and self.alive:
                self.onMessage(response.decode("utf-8"))
                if self.alive:
                    response = self.client.recv(1024)
        except (ConnectionAbortedError,timeout) as event:
            if str(event) == "timed out":
                self._stop(ErrorLevels.OK, ErrorMessages.LOST)
            if self.alive: 
                self._stop(ErrorLevels.ERROR, ErrorMessages.ABORTED)
            else: 
                return 
        if self.alive:
            self._stop(ErrorLevels.OK, ErrorMessages.CLOSED)


if __name__ == "__main__":
    try:
        server = Server()
        server.start()
        while True:
            continue

    except KeyboardInterrupt:
        server.stop()
        server.join()
