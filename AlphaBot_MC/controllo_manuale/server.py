import socket
from threading import Thread
import sqlite3
from AlphaBot_lib import AlphaBot
import time

SERVER_ADDRESS = ("192.168.1.129", 22222)
HEARTBEAT_ADDRESS = ("192.168.1.129", 22223)

BUFFER_SIZE = 4096

# funzione per ricevere e gestire il segnale di vitalità (heartbeat) dal client
def ricevi_segnale_heartbeat(conn_heartbeat, ab):
    
    conn_heartbeat.settimeout(10)   # timeout per rilevare disconnessioni del client
    
    try:
        while True:
            try:
                dati = conn_heartbeat.recv(BUFFER_SIZE).decode()
                
                if dati == "heartbeat":
                    pass  # se ricevo l'heartbeat continuo
                elif not dati:
                    print("Heartbeat assente, chiusura in corso.")
                    break  # se non ricevo l'heartbeat il client si è disconnesso
                
            except socket.timeout:
                print("Timeout heartbeat. Arresto alphabot.")
                ab.setMotor(0, 0)  # fermo l'alphabot in caso di timeout
                
            except Exception as e:
                print(f"Errore ricezione heartbeat: {e}")
                break
    finally:
        conn_heartbeat.close()
        print("Connessione heartbeat chiusa.")

def main():
    # mappatura comandi per movimenti dell'alphabot
    mappa_tasti = {
        "w": (30, 30),     # Avanti
        "s": (-30, -30),   # Indietro
        "a": (30, 0),      # Sinistra
        "d": (0, 30),      # Destra
        "f": (0, 0)        # Ferma
    }

    tasti_premuti = []  # lista per memorizzare i tasti attualmente premuti

    ab = AlphaBot()

    # socket server principale
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_server.bind(SERVER_ADDRESS)
    socket_server.listen()

    ab.stop()  # alphabot all'avvio è fermo

    # socket per la gestione dell'heartbeat
    socket_heartbeat = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_heartbeat.bind(HEARTBEAT_ADDRESS)
    socket_heartbeat.listen(1)
    
    # attesa della connessione del client
    conn_client, client_address = socket_server.accept()
    print(f"Client [{client_address}] connesso")
    
    # connessione per heartbeat
    conn_heartbeat, _ = socket_heartbeat.accept()

    # connessione al database per i movimenti predefiniti
    db = sqlite3.connect('movimenti.db')
    cursor = db.cursor()
    
    # avvio del thread per monitorare heartbeat
    thread_heartbeat = Thread(target = ricevi_segnale_heartbeat, args = (conn_heartbeat, ab))
    thread_heartbeat.start()

    # caricamento comandi dal database
    cursor.execute("SELECT * FROM MOVIMENTO")
    db.commit()
    comandi_database = cursor.fetchall()

    while True:
        messaggio = conn_client.recv(BUFFER_SIZE).decode()
        if not messaggio:
            break  # esce dal loop se il client si disconnette
        
        print(messaggio)
        split_msg = messaggio.split('|')  
        stato, carattere = split_msg[0], split_msg[1][0]

        if stato == "P" and carattere not in tasti_premuti: # se il tasto premuto non è nella lista lo aggiungo
            tasti_premuti.append(carattere)
        elif stato == "R" and carattere in tasti_premuti:   # se il tasto rilasciato è nella lista lo rimuovo
            tasti_premuti.remove(carattere)
                
        motore_1, motore_2 = 0, 0
        for t in tasti_premuti:
            if t == 'f': # "f" è il tasto da premere per far fermare immediatamente l'alphabot
                tasti_premuti.clear()
                ab.setMotor(0, 0)

            elif t in mappa_tasti:
                potenza = mappa_tasti[t]
                motore_1 += potenza[0]
                motore_2 += potenza[1]
                ab.setMotor(motore_1, motore_2)  

if __name__ == '__main__':
    main()
