# database.py
import sqlite3
from models import Utilisateur, Carte, Leader, Deck 

def get_db_connection():
    conn = sqlite3.connect('bdd_cartes.db')
    conn.row_factory = sqlite3.Row
    return conn



def creer_tables():
    conn = get_db_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cartes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT,
                couleur TEXT,
                cout INTEGER,
                puissance INTEGER,
                effet TEXT,
                attributs TEXT,
                reference TEXT,
                niveau_counter INTEGER,
                image_path TEXT
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT,
                couleurs TEXT,
                leader TEXT,
                user_id INTEGER,
                est_public BOOLEAN DEFAULT FALSE,
                leader_id INTEGER,
                FOREIGN KEY (leader_id) REFERENCES leaders(id)
                FOREIGN KEY (user_id) REFERENCES utilisateurs(id)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cartes_decks (
                id_carte INTEGER,
                id_deck INTEGER,
                nombre_exemplaires INTEGER DEFAULT 1,
                FOREIGN KEY (id_carte) REFERENCES cartes (id),
                FOREIGN KEY (id_deck) REFERENCES decks (id),
                PRIMARY KEY (id_carte, id_deck)
            );
        """)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leaders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT,
                couleur TEXT,
                puissance INTEGER,
                effet TEXT,
                attributs TEXT,
                points_de_vie INTEGER,
                reference TEXT,
                image_path TEXT
            );
        ''')

        
def afficher_table(conn, nom_table):
    print(f"Contenu de la table {nom_table}:")
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {nom_table}")
    rows = cur.fetchall()
    for row in rows:
        print(row)
    print("\n")
    

def get_decks(user_id, include_public=False):
    conn = get_db_connection()
    query = '''
        SELECT d.*, l.image_path as leader_image, l.nom as leader_nom
        FROM decks d
        LEFT JOIN leaders l ON d.leader_id = l.id
        WHERE d.user_id = ?
    '''

    if include_public:
        query += ' OR d.est_public = 1'

    decks = conn.execute(query, (user_id,)).fetchall()
    conn.close()
    return [dict(deck) for deck in decks]

def search_cartes(query, colors=None):
    conn = get_db_connection()
    query = f"%{query}%" 
    sql_query = 'SELECT * FROM cartes WHERE (nom LIKE ? OR couleur LIKE ? OR attributs LIKE ? OR effet LIKE ?)'
    params = [query, query, query, query]

    if colors:
        placeholders = ', '.join(['?'] * len(colors))
        sql_query += f' AND couleur IN ({placeholders})'
        params.extend(colors)

    cartes = conn.execute(sql_query, params).fetchall()
    conn.close()

    return [dict(carte) for carte in cartes]


def add_deck(deck):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO decks (user_id, nom, couleurs, leader_id) VALUES (?, ?, ?, ?)
    ''', (deck.user_id, deck.nom, deck.couleurs, deck.leader_id))
    conn.commit()
    conn.close()



def get_user_db_connection():
    conn = sqlite3.connect('userdb.db')
    conn.row_factory = sqlite3.Row
    return conn


def creer_table_utilisateurs():
    conn = get_user_db_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT,
                email TEXT UNIQUE,
                motDePasse TEXT
            );
        """)
    conn.close()

def ajouter_carte_au_deck(deck_id, identifiant, nombre_exemplaires, par_reference=False):
    conn = get_db_connection()

    # Si l'ajout se fait par référence, cherchez d'abord l'ID de la carte
    if par_reference:
        carte = conn.execute('SELECT id FROM cartes WHERE reference = ?', (identifiant,)).fetchone()
        if carte:
            carte_id = carte['id']
        else:
            print("Carte non trouvée avec la référence:", identifiant)
            conn.close()
            return
    else:
        carte_id = identifiant

    # La logique existante pour ajouter la carte au deck
    existant = conn.execute('''
        SELECT nombre_exemplaires FROM cartes_decks 
        WHERE id_deck = ? AND id_carte = ?
    ''', (deck_id, carte_id)).fetchone()

    if existant:
        #Si + de 4 exemplaires de la cate dans le deck alors 4 exemplaires
        nouveau_nombre = min(4, existant['nombre_exemplaires'] + nombre_exemplaires)
        conn.execute('''
            UPDATE cartes_decks SET nombre_exemplaires = ?
            WHERE id_deck = ? AND id_carte = ?
        ''', (nouveau_nombre, deck_id, carte_id))
    else:
        conn.execute('''
            INSERT INTO cartes_decks (id_carte, id_deck, nombre_exemplaires) 
            VALUES (?, ?, ?)
        ''', (carte_id, deck_id, nombre_exemplaires))

    conn.commit()
    conn.close()


def get_all_cartes(colors=None):
    conn = get_db_connection()
    query = 'SELECT * FROM cartes'
    params = []

    if colors:
        placeholders = ', '.join(['?'] * len(colors))
        query += f' WHERE couleur IN ({placeholders})'
        params = colors

    cartes = conn.execute(query, params).fetchall()
    conn.close()

    # Ajout pour le débogage
    print("Query:", query)
    print("Params:", params)
    print("Cartes trouvées:", len(cartes))
    print(cartes)

    cartes_liste = [dict(carte) for carte in cartes]
    for carte in cartes_liste:
        if 'image_path' in carte and carte['image_path']:
            carte['image_path'] = carte['image_path'].replace('\\', '/')

    return cartes_liste



def get_cartes_from_deck(deck_id):
    conn = get_db_connection()
    cartes = conn.execute('''
        SELECT c.*, cd.nombre_exemplaires FROM cartes c
        INNER JOIN cartes_decks cd ON c.id = cd.id_carte
        WHERE cd.id_deck = ?
    ''', (deck_id,)).fetchall()
    cartes_list = [dict(carte) for carte in cartes]
    for carte in cartes_list:
        if carte['image_path']:
            carte['image_path'] = carte['image_path'].replace('\\', '/')
    conn.close()
    return cartes_list


def ajouter_carte(carte :Carte):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO cartes (nom, couleur, cout, puissance, attributs, reference, niveau_counter, image_path, effet) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (carte.nom, carte.couleur, carte.cout, carte.puissance, carte.attributs, carte.reference, carte.niveauCounter, carte.imagePath, carte.effet))
    conn.commit()
    conn.close()
    return carte


def ajouter_leader(leader :Leader):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO leaders (nom, couleur, puissance, effet, attributs, points_de_vie, reference, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (leader.nom, leader.couleur, leader.puissance, leader.effet, leader.attributs, leader.points_de_vie, leader.reference, leader.imagePath))
    conn.commit()
    conn.close()


def ajouter_leader_id_aux_decks():
    conn = get_db_connection()
    with conn:
        conn.execute('ALTER TABLE decks ADD COLUMN leader_id INTEGER REFERENCES leaders(id)')
    conn.close()

def get_all_leaders():
    conn = get_db_connection()
    leaders = conn.execute('SELECT * FROM leaders').fetchall()
    conn.close()
    return leaders

def get_leader_from_deck(deck_id):
    conn = get_db_connection()
    leader = conn.execute('''
        SELECT l.* FROM leaders l
        JOIN decks d ON l.id = d.leader_id
        WHERE d.id = ?
    ''', (deck_id,)).fetchone()
    conn.close()

    if leader:
        leader_dict = dict(leader)
        if leader_dict['image_path']:
            leader_dict['image_path'] = leader_dict['image_path'].replace('\\', '/')
        return leader_dict
    return None

def supprimer_carte_de_deck(deck_id, carte_id, nombre_exemplaires):
    conn = get_db_connection()
    # Récupérer le nombre d'exemplaires actuel
    current_exemplaires = conn.execute('''
        SELECT nombre_exemplaires FROM cartes_decks 
        WHERE id_deck = ? AND id_carte = ?
    ''', (deck_id, carte_id)).fetchone()

    if current_exemplaires and current_exemplaires['nombre_exemplaires'] > nombre_exemplaires:
        # Mettre à jour le nombre d'exemplaires
        new_exemplaires = current_exemplaires['nombre_exemplaires'] - nombre_exemplaires
        conn.execute('''
            UPDATE cartes_decks
            SET nombre_exemplaires = ?
            WHERE id_deck = ? AND id_carte = ?
        ''', (new_exemplaires, deck_id, carte_id))
    elif current_exemplaires:
        # Si le nombre demandé est égal ou supérieur, supprimer la ligne
        conn.execute('''
            DELETE FROM cartes_decks WHERE id_deck = ? AND id_carte = ?
        ''', (deck_id, carte_id))

    conn.commit()
    conn.close()



def get_deck_details(deck_id):
    conn = get_db_connection()
    deck_row = conn.execute('SELECT * FROM decks WHERE id = ?', (deck_id,)).fetchone()
    conn.close()
    if deck_row:
        deck = dict(deck_row)
        return deck
    return None




def get_carte_details(carte_id):
    conn = get_db_connection()
    carte = conn.execute('SELECT * FROM cartes WHERE id = ?', (carte_id,)).fetchone()
    conn.close()
    return dict(carte)

def compter_cartes_dans_deck(deck_id):
    conn = get_db_connection()
    total = conn.execute('''
        SELECT SUM(nombre_exemplaires) as total FROM cartes_decks 
        WHERE id_deck = ?
    ''', (deck_id,)).fetchone()
    conn.close()
    return total['total'] if total['total'] is not None else 0

def get_leader_details(leader_id):
    conn = get_db_connection()
    leader = conn.execute('SELECT * FROM leaders WHERE id = ?', (leader_id,)).fetchone()
    conn.close()
    if leader:
        return dict(leader)
    else:
        return None
    
def get_leader_color_from_db(leader_id):
    conn = get_db_connection()
    try:
        leader = conn.execute('SELECT couleur FROM leaders WHERE id = ?', (leader_id,)).fetchone()
        if leader and 'couleur' in leader:
            return leader['couleur'].split(', ')
        return []
    finally:
        conn.close()


def supprimer_deck(deck_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM decks WHERE id = ?', (deck_id,))
    conn.execute('DELETE FROM cartes_decks WHERE id_deck = ?', (deck_id,))
    conn.commit()
    conn.close()
    
def ajouter_utilisateur(utilisateur: Utilisateur):
    conn = get_user_db_connection()
    try:
        conn.execute('INSERT INTO utilisateurs (nom, email, motDePasse) VALUES (?, ?, ?)',
                     (utilisateur.nom, utilisateur.email, utilisateur.motDePasse))
        conn.commit()
    finally:
        conn.close()


def get_utilisateur_par_email(email: str):
    conn = get_user_db_connection()
    user_data = conn.execute('SELECT * FROM utilisateurs WHERE email = ?', (email,)).fetchone()
    conn.close()
    if user_data:
        return Utilisateur(user_data['nom'], user_data['email'], user_data['motDePasse'])
    return None

def get_carte_details_par_reference(ref_carte):
    # Fonction pour récupérer les détails de la carte à partir de la référence
    conn = get_db_connection()
    carte = conn.execute('SELECT * FROM cartes WHERE reference = ?', (ref_carte,)).fetchone()
    conn.close()
    return carte
