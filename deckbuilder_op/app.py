 # app.py
import os
import random
from random import choices
import sqlite3
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from models import Utilisateur, Carte, Leader, Deck
from database import get_carte_details_par_reference, get_utilisateur_par_email, ajouter_utilisateur, creer_tables, get_db_connection,supprimer_deck, search_cartes, get_decks, add_deck, afficher_table, get_user_db_connection, creer_table_utilisateurs, ajouter_carte_au_deck, get_all_cartes, get_cartes_from_deck, ajouter_carte, ajouter_leader,ajouter_leader_id_aux_decks, get_all_leaders, get_leader_from_deck, get_deck_details, supprimer_carte_de_deck, get_carte_details, compter_cartes_dans_deck, get_leader_details, get_leader_color_from_db
creer_table_utilisateurs()

creer_tables()


conn = get_db_connection()


afficher_table(conn, "cartes")
afficher_table(conn, "decks")
afficher_table(conn, "cartes_decks")


conn.close()

app = Flask(__name__)
app.secret_key = '4697'
@app.route('/')
def index():
    return redirect(url_for('show_decks'))

@app.route('/decks')
def show_decks():
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login'))
    
    search_query = request.args.get('search', '')  # Récupérer le terme de recherche, chaîne vide par défaut
    conn = get_db_connection()
    
    if search_query:
        search_query = f"%{search_query}%".lower()
        decks_user_query = '''
            SELECT d.*, l.image_path as leader_image, l.nom as leader_nom
            FROM decks d
            LEFT JOIN leaders l ON d.leader_id = l.id
            WHERE d.user_id = ? AND (LOWER(d.nom) LIKE ? OR LOWER(l.nom) LIKE ?)
        '''
        decks_publics_query = '''
            SELECT d.*, l.image_path as leader_image, l.nom as leader_nom
            FROM decks d
            LEFT JOIN leaders l ON d.leader_id = l.id
            WHERE d.est_public = 1 AND d.user_id != ? AND (LOWER(d.nom) LIKE ? OR LOWER(l.nom) LIKE ?)
        '''
        decks_user = conn.execute(decks_user_query, (user_id, search_query, search_query)).fetchall()
        decks_publics = conn.execute(decks_publics_query, (user_id, search_query, search_query)).fetchall()
    else:
        # Sinon, récupérer tous les decks de l'utilisateur et les decks publics
        decks_user = get_decks(user_id)
        decks_publics = conn.execute('''
            SELECT d.*, l.image_path as leader_image, l.nom as leader_nom
            FROM decks d
            LEFT JOIN leaders l ON d.leader_id = l.id
            WHERE d.est_public = 1 AND d.user_id != ?
        ''', (user_id,)).fetchall()

    conn.close()

    decks_with_leaders_user = [{'deck': dict(deck), 'leader': get_leader_from_deck(deck['id'])} for deck in decks_user]
    decks_with_leaders_public = [{'deck': dict(deck), 'leader': get_leader_from_deck(deck['id'])} for deck in decks_publics]

    return render_template('decks.html', search_query=search_query, decks_user=decks_with_leaders_user, decks_public=decks_with_leaders_public)


@app.route('/add_deck', methods=['GET', 'POST'])
def add_deck_route():
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login'))

    leaders = get_all_leaders()

    if request.method == 'POST':
        deck_name = request.form['deck_name']
        leader_id = request.form['leader_id']
        
        # Récupérez le leader à partir de l'ID du leader
        leader = get_leader_details(leader_id)
        if leader:
            leader_colors = leader['couleur'].split(', ')
        else:
            leader_colors = []

        # Convertir la liste des couleurs en une chaîne
        colors_str = ', '.join(leader_colors) if leader_colors else ''

        nouveau_deck = Deck(user_id, deck_name, colors_str,  leader_id)
        add_deck(nouveau_deck)
        return redirect(url_for('show_decks'))

    return render_template('add_deck.html', leaders=leaders)

def simulate_hand(deck_id):
    conn = get_db_connection()
    # Récupérer toutes les cartes du deck avec leur nombre d'exemplaires
    cartes = conn.execute('''
        SELECT c.id, c.nom, c.image_path, cd.nombre_exemplaires FROM cartes c
        JOIN cartes_decks cd ON c.id = cd.id_carte
        WHERE cd.id_deck = ?
    ''', (deck_id,)).fetchall()
    conn.close()

    # Convertir les chemins d'images en utilisant des barres obliques (/)
    cartes_corrected = [{'id': carte['id'], 
                         'nom': carte['nom'], 
                         'image_path': carte['image_path'].replace('\\', '/'),
                         'nombre_exemplaires': carte['nombre_exemplaires']} 
                        for carte in cartes]

    # Créer une liste de cartes en fonction du nombre d'exemplaires
    cartes_ponderees = [(carte['id'], carte['nom'], carte['image_path']) 
                        for carte in cartes_corrected 
                        for _ in range(carte['nombre_exemplaires'])]

    if len(cartes_ponderees) >= 5:
        main_aleatoire = random.sample(cartes_ponderees, 5)
    else:
        main_aleatoire = cartes_ponderees

    return [{'id': carte[0], 'nom': carte[1], 'image_path': carte[2]} for carte in main_aleatoire]


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        nom = request.form['nom']
        email = request.form['email']
        motDePasse = request.form['motDePasse']

        utilisateur = Utilisateur(nom, email, motDePasse)
        ajouter_utilisateur(utilisateur)
        return redirect(url_for('login'))

    return render_template('signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        motDePasse = request.form['motDePasse']

        conn = get_user_db_connection()
        user_data = conn.execute('SELECT * FROM utilisateurs WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user_data and user_data['motDePasse'] == motDePasse:
            session['user_id'] = user_data['id']
            return redirect(url_for('show_decks'))  # Redirection vers la page des decks
        else:
            # Si les identifiants ne sont pas corrects, affichez un message d'erreur
            return render_template('login.html', error="Email ou mot de passe incorrect")

    return render_template('login.html')



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/edit_deck/<int:deck_id>', methods=['GET', 'POST'])
def edit_deck(deck_id):
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login'))

    conn = get_db_connection()
    deck = get_deck_details(deck_id)
    if not deck or deck['user_id'] != user_id:
        conn.close()
        return "Accès non autorisé", 403

    if request.method == 'POST':
        selected_cartes = request.form.getlist('carte_id')
        for carte_id in selected_cartes:
            nombre_exemplaires = int(request.form.get(f'nombre_exemplaires_{carte_id}', 1))
            ajouter_carte_au_deck(deck_id, int(carte_id), nombre_exemplaires)
        est_public = request.form.get('est_public') == 'on'
        conn.execute('UPDATE decks SET est_public = ? WHERE id = ?', (est_public, deck_id))
        conn.commit()
        conn.close()
        return redirect(url_for('view_deck', deck_id=deck_id))

    search_query = request.args.get('search', '')  # Récupère la requête de recherche à partir de l'URL

    deck_colors = deck['couleurs'].split(',') if deck['couleurs'] else []
    toutes_les_cartes = search_cartes(search_query, deck_colors) if search_query else get_all_cartes(colors=deck_colors)

    cartes_du_deck = get_cartes_from_deck(deck_id)
    conn.close()

    return render_template(
        'edit_deck.html',
        toutes_les_cartes=toutes_les_cartes,
        cartes_du_deck=cartes_du_deck,
        deck=deck,
        deck_id=deck_id,
        search_query=search_query
    )

# Supposons que la fonction search_cartes ressemble à ceci dans database.py :
def search_cartes(search_query, colors):
    conn = get_db_connection()
    query = "SELECT * FROM cartes WHERE (nom LIKE ? OR couleur LIKE ? OR attributs LIKE ?) AND couleur IN ({})"
    to_filter = colors
    to_search = f"%{search_query}%"
    placeholders = ', '.join('?' for _ in colors)  # Crée des placeholders pour la clause IN
    query = query.format(placeholders)
    cartes = conn.execute(query, [to_search, to_search, to_search] + to_filter).fetchall()
    conn.close()
    return [dict(carte) for carte in cartes]


# Ajoutez cette nouvelle fonction de recherche dans votre fichier database.py
def search_cartes(query, colors=None):
    conn = get_db_connection()
    query = f"%{query}%"  # Prépare la requête pour une recherche partielle avec LIKE
    sql_query = 'SELECT * FROM cartes WHERE (nom LIKE ? OR couleur LIKE ? OR attributs LIKE ? OR effet LIKE ?)'
    params = [query, query, query, query]

    if colors:
        placeholders = ', '.join(['?'] * len(colors))
        sql_query += f' AND couleur IN ({placeholders})'
        params.extend(colors)

    cartes = conn.execute(sql_query, params).fetchall()
    conn.close()

    return [dict(carte) for carte in cartes]


@app.route('/add_carte', methods=['GET', 'POST'])
def add_carte():
    user_id = session.get('user_id')
    is_admin = user_id == 1 

    if not is_admin:
        return "Accès non autorisé", 403
    if request.method == 'POST':
        nom = request.form['nom']
        couleur = request.form['couleur']
        cout = request.form['cout']
        puissance = request.form['puissance']
        attributs = request.form['attributs']
        reference = request.form['reference']
        niveau_counter = request.form['niveau_counter']
        effet = request.form['effet']

        # Traitement de l'image téléchargée
        image = request.files['image']
        if image:
           filename = secure_filename(image.filename)
           image_path = os.path.join('images', filename)  # Enregistrez ce chemin sans 'static/'
           full_image_path = os.path.join(app.static_folder, image_path)
           image.save(full_image_path)

           # Ajoutez la carte à la base de données
           #ajouter_carte(nom, couleur, cout, puissance, attributs, reference, niveau_counter, image_path, effet) 
        carteToCreate = Carte(nom, couleur, cout, puissance, attributs, reference, niveau_counter, image_path, effet)
        print("Created carte : "+str(ajouter_carte(carteToCreate)))
        return redirect(url_for('add_carte'))

    return render_template('add_carte.html')


@app.route('/view_deck/<int:deck_id>')
def view_deck(deck_id):
    deck = get_deck_details(deck_id)
    if not deck:
        return "Deck not found", 404  
    cartes = get_cartes_from_deck(deck_id)
    total_cartes = compter_cartes_dans_deck(deck_id)
    leader = get_leader_from_deck(deck_id)
    return render_template('view_deck.html', deck=deck, cartes=cartes, total_cartes=total_cartes, leader=leader)

@app.route('/list_all_cartes_api')
def list_all_cartes():
    cartes = get_all_cartes()
    if not cartes:
        return "Cards not found", 404  
    return str(cartes), 200

@app.route('/liste_cartes')
def liste_cartes():
    cartes = get_all_cartes()
    if not cartes:
        return "Cards not found", 404
    return render_template('liste_cartes.html', cartes=cartes)

@app.route('/carte_details/<int:carte_id>')
def carte_details(carte_id):
    carte = get_carte_details(carte_id)
    return jsonify(carte)


@app.route('/add_leader', methods=['GET', 'POST'])
def add_leader():
    user_id = session.get('user_id')
    is_admin = user_id == 1  # Vérifie si l'utilisateur actuel a l'ID 1

    if not is_admin:
        return "Accès non autorisé", 403
    if request.method == 'POST':
        nom = request.form['nom']
        couleur = request.form['couleur']
        puissance = request.form['puissance']
        effet = request.form['effet']
        attributs = request.form['attributs']
        points_de_vie = request.form['points_de_vie']
        reference = request.form['reference']
        image = request.files['image']
        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join('images', filename)  
            full_image_path = os.path.join(app.static_folder, image_path)
            image.save(full_image_path)
            
            LeaderToCreate = Leader(nom, couleur, puissance, effet, attributs, points_de_vie, reference, image_path)
            print("Created carte : "+str(ajouter_leader(LeaderToCreate)))
        return redirect(url_for('index'))

    return render_template('add_leader.html')

@app.route('/delete_carte_from_deck/<int:deck_id>/<int:carte_id>', methods=['POST'])
def delete_carte_from_deck(deck_id, carte_id):
    nombre_exemplaires = int(request.form['nombre_exemplaires'])
    supprimer_carte_de_deck(deck_id, carte_id, nombre_exemplaires)
    return redirect(url_for('view_deck', deck_id=deck_id))

@app.route('/get_leader_color/<int:leader_id>')
def get_leader_color(leader_id):
    leader_details = get_leader_details(leader_id)
    if leader_details:
        return jsonify({'color': leader_details['couleur']})
    else:
        return jsonify({'error': 'Leader not found'}), 404
    
@app.route('/simulate_hand/<int:deck_id>')
def simulate_hand_route(deck_id):
    main_aleatoire = simulate_hand(deck_id)
    return render_template('simulate_hand.html', main_aleatoire=main_aleatoire)

@app.route('/delete_deck/<int:deck_id>', methods=['POST'])
def delete_deck(deck_id):
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login'))

    supprimer_deck(deck_id) 
    return redirect(url_for('show_decks'))

@app.route('/ajouter_cartes_par_liste/<int:deck_id>', methods=['POST'])
def ajouter_cartes_par_liste(deck_id):
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login'))

    deck_list = request.form.get('deck_list')
    if deck_list:
        traiter_deck_list(deck_list, deck_id)

    return redirect(url_for('view_deck', deck_id=deck_id))

def traiter_deck_list(deck_list, deck_id):
    # Récupérer les informations du leader
    leader = get_leader_from_deck(deck_id)
    couleurs_leader = [couleur.strip().lower() for couleur in leader['couleur'].split(',')] if leader else []
    total_cartes = compter_cartes_dans_deck(deck_id)

    for ligne in deck_list.splitlines():
        if 'x' in ligne:
            quantite, ref_carte = ligne.split('x', 1)
            quantite = int(quantite.strip())
            ref_carte = ref_carte.strip()

            # Vérifiez si la carte existe et récupérez ses détails
            carte = get_carte_details_par_reference(ref_carte)
            if not carte:
                print(f"Carte non trouvée avec la référence: {ref_carte}")
                continue

            couleurs_carte = [couleur.strip().lower() for couleur in carte['couleur'].split(',')]

            # Vérifiez si au moins une couleur de la carte correspond à une couleur du leader
            if not any(couleur in couleurs_leader for couleur in couleurs_carte):
                print(f"La carte {carte['nom']} ne correspond pas aux couleurs du leader.")
                continue

            # Vérifiez le nombre d'exemplaires
            if quantite > 4:
                print(f"Nombre d'exemplaires trop élevé pour la carte {carte['nom']}. Limité à 4.")
                quantite = 4

            # Vérifiez si l'ajout dépasse le nombre maximal de cartes dans le deck
            if total_cartes + quantite > 50:
                print(f"Ajout de cartes refusé. Le deck a déjà {total_cartes} cartes.")
                continue

            # Ajoutez la carte au deck
            ajouter_carte_au_deck(deck_id, carte['id'], quantite)
            total_cartes += quantite




if __name__ == '__main__':
    app.run(debug=True)
    
