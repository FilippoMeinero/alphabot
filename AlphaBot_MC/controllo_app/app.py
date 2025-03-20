from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from AlphaBot_lib import AlphaBot
import jwt
import datetime
import sqlite3

SECRET_KEY = ("progettoAlphabot")

app = Flask(__name__)

ab = AlphaBot()
ab.stop()

# funzione per ottenere gli utenti registrati nel database
def dati_utenti():
    connessione = sqlite3.connect('./users.db')  # connessione al database 
    cursore = connessione.cursor()
    cursore.execute("SELECT * FROM utenti")  # recupero di tutti gli utenti registrati
    risultati = cursore.fetchall()  
    dizionario = {r[0]: r[1] for r in risultati}  # creazione di un dizionario con email e password
    connessione.close()
    return dizionario

# funzione per inizializzare il database e creare la tabella utenti (se non esiste)
def inizializza_database():
    connessione = sqlite3.connect('./users.db')
    cursore = connessione.cursor()
    cursore.execute('''
        CREATE TABLE IF NOT EXISTS utenti (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    connessione.commit()
    connessione.close()

# funzione per verificare le credenziali di accesso
def verifica_credenziali(email, password):
    credenziali = dati_utenti()  # recupero utenti registrati
    if email in credenziali:
        hash_memorizzato = credenziali[email]  
        print(f"memorizzato: {hash_memorizzato} password: {password}")
        # controllo se la password fornita corrisponde a quella hashata memorizzata
        if check_password_hash(hash_memorizzato, password):
            return True
    return False

# funzione per registrare un nuovo utente nel database
def registra_nuovo_utente(email, password):
    password_criptata = generate_password_hash(password)  # hash della password
    credenziali = dati_utenti()
    if email not in credenziali:  # verifica se l'email è già registrata
        connessione = sqlite3.connect('./users.db')
        cursore = connessione.cursor()
        cursore.execute("INSERT INTO utenti (email, password) VALUES (?, ?)", (email, password_criptata))
        connessione.commit()
        connessione.close()
        return True
    return False

# rotta per la pagina iniziale, controlla se l'utente è loggato tramite cookie
@app.route("/")
def pagina_iniziale():
    token_utente = request.cookies.get("utente_loggato")
    if token_utente:
        return redirect(url_for('pagina_principale'))
    return redirect(url_for('accesso'))

# rotta per la gestione dell'accesso degli utenti
@app.route("/accesso", methods=['POST', 'GET'])
def accesso():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if verifica_credenziali(email, password):  # controllo delle credenziali
            print("Accesso completato con successo")
            # generazione di un token JWT con scadenza a 1 giorno
            scadenza = datetime.datetime.utcnow() + datetime.timedelta(days=1)
            token = jwt.encode({"email": email, "exp": scadenza}, SECRET_KEY, algorithm="HS256")
            risposta = make_response(redirect(url_for('pagina_principale')))
            # salvataggio del token nei cookie con protezione httponly
            risposta.set_cookie("utente_loggato", token, httponly=True, samesite="Strict", max_age=60*60*24)
            print(f"token: {token}")
            return risposta
        else:
            print("Accesso fallito - Credenziali non valide")
            return render_template("accesso.html", messaggio="Email o password non valide")
    return render_template("accesso.html")

# rotta per la registrazione di un nuovo utente
@app.route("/registrazione", methods=['GET', 'POST'])
def registrazione():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if registra_nuovo_utente(email, password):  # registra il nuovo utente se non esiste già
            return redirect(url_for('accesso'))
        else:
            return render_template("registrazione.html", messaggio="Email già registrata")
    return render_template("registrazione.html")

# rotta per la pagina principale dell'app
@app.route("/pagina_principale", methods=['GET', 'POST'])
def pagina_principale():
    token_utente = request.cookies.get("utente_loggato")
    if not token_utente:  # se il token non esiste, reindirizza alla pagina di accesso
        return redirect(url_for('accesso'))
    else:
        # decodifica del token JWT per ottenere i dati dell'utente
        dati_decodificati = jwt.decode(token_utente, SECRET_KEY, algorithms=["HS256"])
        print(f"token_utente: {token_utente}")
        return render_template("controllo.html")

# rotta per la disconnessione dell'utente, elimina il cookie di autenticazione
@app.route("/disconnessione")
def disconnessione():
    risposta = make_response(redirect(url_for('accesso')))
    risposta.delete_cookie("utente_loggato")  # rimozione del cookie
    return risposta

# rotta per controllare il movimento del robot AlphaBot
@app.route("/controllo", methods=['POST', 'GET'])
def controllo():
    token_utente = request.cookies.get("utente_loggato")
    if not token_utente:
        return redirect(url_for('accesso'))
    else:
        if request.method == 'POST':
            # controllo dei comandi inviati dal form e movimento del robot
            if request.form.get('AVANTI') == 'AVANTI':
                print("movimento: avanti")
                ab.forward()
            elif request.form.get('INDIETRO') == 'INDIETRO':
                print("movimento: indietro")
                ab.backward()
            elif request.form.get('SINISTRA') == 'SINISTRA':
                print("movimento: sinistra")
                ab.left()
            elif request.form.get('DESTRA') == 'DESTRA':
                print("movimento: destra")
                ab.right()
            elif request.form.get('FERMO') == 'FERMO':
                print("movimento: fermo")
                ab.stop()
            else:
                print("Comando sconosciuto")
        return render_template("controllo.html")

# avvio dell'applicazione Flask con inizializzazione del database
if __name__ == '__main__':
    inizializza_database()  
    app.run(debug=True, host='0.0.0.0')
