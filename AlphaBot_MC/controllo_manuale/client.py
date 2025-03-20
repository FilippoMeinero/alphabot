from threading import Thread
import socket
import time
from pynput import keyboard

SERVER_ADDRESS = ("192.168.1.129", 22222)
HEARTBEAT_ADDRESS = ("192.168.1.129", 22223) 

termina_heartbeat = False  # controllo per terminare il thread heartbeat

conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conn.connect(SERVER_ADDRESS)  # Connessione al server


tasti_premuti = []  # lista per memorizzare i tasti premuti

# funzione per inviare periodicamente segnali di heartbeat al server
def invia_segnale_heartbeat():
    global termina_heartbeat
    conn_heartbeat = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn_heartbeat.connect(HEARTBEAT_ADDRESS)  # connessione al server heartbeat
    
    while not termina_heartbeat:
        try:
            conn_heartbeat.sendall("heartbeat".encode())  # invia un segnale ogni secondo
            time.sleep(1)
        except Exception as e:
            print(f"Errore nel thread di heartbeat: {e}")
            break  # se c'è un errore esce dal ciclo
    
    conn_heartbeat.close()
    print("Connessione di heartbeat terminata.")

# funzione chiamata quando un tasto viene premuto
def alla_pressione(tasto):
    carattere = tasto.char
    if carattere not in tasti_premuti:
        tasti_premuti.append(carattere)
        messaggio = f"P|{carattere}"  # "P" = "premuto"
        print(messaggio)
        conn.sendall(messaggio.encode())  # invia il comando al server

# funzione chiamata quando un tasto viene rilasciato
def al_rilascio(tasto):
    carattere = tasto.char
    print(carattere)

    if carattere in tasti_premuti:
        tasti_premuti.remove(carattere)
    messaggio = f"R|{carattere}"  # "R" = "rilasciato"
    print(messaggio)
    conn.sendall(messaggio.encode())  # invia il comando al server
    time.sleep(0.001)  # breve pausa per evitare troppi invii consecutivi

# funzione per attivare il monitoraggio della tastiera
def avvia_ascolto_tastiera():
    with keyboard.Listener(on_press = alla_pressione, on_release = al_rilascio) as listener:
        listener.join()

def main():
    global termina_heartbeat 
    thread_heartbeat = Thread(target = invia_segnale_heartbeat)
    thread_heartbeat.start()
    
    avvia_ascolto_tastiera()    # avvio del listener della tastiera
    
    # terminazione del thread heartbeat quando il client viene chiuso
    termina_heartbeat = True
    thread_heartbeat.join()
    conn.close()
    print("Connessione chiusa.")
        
if __name__ == '__main__':
    main()
