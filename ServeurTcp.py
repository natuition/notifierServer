from socket import socket, AF_INET, SOCK_STREAM, timeout
from threading import Thread
import json
from notifier import Notifier
import schedule
import time
import utility

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
        self.notifier.sendTelegramMsg(self.tokens["telegram"],self.tokens["chat_id"],"Serveur de notification lancé !",list(),False)
        self.running = True
        self.socket.listen(5)
        while self.running:
            try:
                client, address = self.socket.accept()
            except timeout:
                continue
            if DEBUG:
                print(f"[{address[0]}] connected")
            
            msg = f"{self.robots[address[0]]} : " + self.translate["Messages"]["Robot_ON"]["fr"]
            self.notifier.sendTelegramMsg(self.tokens["telegram"],self.tokens["chat_id"],msg,list(),False)
            client_handling = ClientHandling(client, address, self.client_handling_stopped,self.robots[address[0]])
            client_handling.start()
            self.client_pool.append(client_handling)


class ClientHandling(Thread):

    def __init__(self, client, address, exit_callback, sn):
        Thread.__init__(self)
        self.client = client
        self.address = address
        self.sn = sn
        self.exit_callback = exit_callback
        self.alive = True
        self.path_gps_with_extract = None
        self.resume_session = None
        self.current_ext = dict()
        self.client.settimeout(10)

    def _stop(self, error_level: ErrorLevels, error_msg: ErrorMessages):
        self.alive = False
        self.close_connection()
        if self.path_gps_with_extract is not None:
            self.path_gps_with_extract.close()
        if self.resume_session is not None:
            self.resume_session.close()
        self.exit_callback(self, error_level, error_msg)

    def close_connection(self):
        self.alive = False
        self.client.close()
        if DEBUG:
            print(f"[{self.address[0]}] disconnected")

    def onMessage(self, message):
        if SyntheseRobot.HS in message:
            self._stop(ErrorLevels.OK, SyntheseRobot.HS)
        elif ";" in message:

            infos = message.split(";")
            if infos[1] == SyntheseRobot.OP:

                if self.path_gps_with_extract is None:
                    self.path_gps_with_extract = utility.Logger(f"{self.sn}/{infos[0]}/path_gps_with_extract.txt", add_time=False)
                
                if len(infos) == 4:
                    self.path_gps_with_extract.write_and_flush(f"{infos[2]} : {infos[3]}\n")
                    for key, value in eval(infos[3]).items():
                        if key not in self.current_ext:
                            self.current_ext[key] = value
                        else:
                            self.current_ext[key] += value
                else:
                    self.path_gps_with_extract.write_and_flush(f"{infos[2]}\n")

                if self.resume_session is not None:
                    if len(infos) == 4:
                        self.resume_session.remove_end_line()
                        self.resume_session.remove_end_line()
                        self.resume_session.write_and_flush(f"Extraction number : {self.current_ext}\n")
                    else:
                        self.resume_session.remove_end_line()
                    self.resume_session.write_and_flush(f"End time : {utility.get_current_time()}")

            elif infos[0] == "START":
                utility.create_directories(self.sn)
                utility.create_directories(f"{self.sn}/{infos[1]}")
                self.field = utility.Logger(f"{self.sn}/{infos[1]}/field.txt", add_time=False)
                for coord in eval(infos[4]):
                    self.field.write_and_flush(f"{coord}\n")
                self.field.close()
                self.resume_session = utility.Logger(f"{self.sn}/{infos[1]}/session_resume.txt", add_time=False)
                self.resume_session.write_and_flush(f"Start time : {infos[1]}\n")
                self.resume_session.write_and_flush(f"Voltage at start : {infos[2]}\n")
                self.resume_session.write_and_flush(f"Treated plant : {infos[3]}\n")
                self.resume_session.write_and_flush("Extraction number : {}\n")
                self.resume_session.write_and_flush("End time :")
            elif infos[0] == "STOP":
                if self.resume_session is not None:
                    if len(infos) == 3:
                        self.resume_session.remove_end_line()
                        self.resume_session.remove_end_line()
                        self.resume_session.write_and_flush(f"Extraction number : {infos[2]}\n")
                    else:
                        self.resume_session.remove_end_line()
                    self.resume_session.write_and_flush(f"End time : {utility.get_current_time()}")
                            
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

def say_hello():
    notifier = Notifier()
    with open('./config.json') as json_file:
        config = json.load(json_file)
        tokens = config["Tokens"]
        notifier.sendTelegramMsg(tokens["telegram"],tokens["chat_id"],"Bonjour, bonne journée à vous ;)",list(),False)
    

if __name__ == "__main__":
    schedule.every().day.at("06:00").do(say_hello)
    try:
        server = Server()
        server.start()
        while True:
            schedule.run_pending()
            time.sleep(1)
            continue

    except KeyboardInterrupt:
        server.stop()
        server.join()
