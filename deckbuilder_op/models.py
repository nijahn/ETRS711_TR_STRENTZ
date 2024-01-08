# models.py
class Utilisateur:
    def __init__(self, nom, email, motDePasse):
        self.id = None
        self.nom = nom
        self.email = email
        self.motDePasse = motDePasse
        self.decks = []

    def creerDeck(self, nom, couleurs, leader, cartes, conn):
        deck = Deck(nom, couleurs, leader)
        for carte in cartes:
            deck.ajouterCarte(carte)
        self.decks.append(deck)
        deck.sauvegarder(conn)  # Sauvegarde le deck dans la base de données
        return deck

    def supprimerDeck(self, deck, conn):
        if deck in self.decks:
            self.decks.remove(deck)
            with conn:
                conn.execute("""
                    DELETE FROM cartes_decks WHERE id_deck = ?;
                """, (deck.id,))  # Assurez-vous d'avoir l'ID du deck
                conn.execute("""
                    DELETE FROM decks WHERE id = ?;
                """, (deck.id,))

    def afficherDecks(self):
        return '\n'.join([deck.afficher() for deck in self.decks])

class Carte:
    def __init__(self, nom, couleur, cout, puissance, attributs, reference, niveauCounter, imagePath, effet):
        self.nom = nom
        self.couleur = couleur
        self.cout = cout
        self.puissance = puissance
        self.attributs = attributs
        self.reference = reference
        self.niveauCounter = niveauCounter
        self.imagePath = imagePath
        self.effet = effet

    def sauvegarder(self, conn):
        with conn:
            cur = conn.cursor()  # Utilisation d'un curseur
            cur.execute("""
                INSERT INTO cartes (nom, couleur, cout, puissance, attributs, reference, niveau_counter)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (self.nom, self.couleur, self.cout, self.puissance, ','.join(self.attributs), self.reference, self.niveauCounter))
            self.id = cur.lastrowid
            return cur.lastrowid  # Retourne l'ID de la carte insérée avec le curseur

class Leader(Carte):
    def __init__(self, nom, couleur, puissance, effet, attributs, points_de_vie, reference, imagePath):
        default_cout = 0  # Default value for cout
        default_niveauCounter = 0  # Default value for niveauCounter

        super().__init__(nom, couleur, default_cout, puissance, attributs, reference, default_niveauCounter, imagePath, effet)
        self.points_de_vie = points_de_vie


class Deck:
    def __init__(self, user_id, nom, couleurs, leader_id):
        self.user_id = user_id
        self.nom = nom
        self.couleurs = couleurs
        self.leader_id = leader_id

    def ajouterCarte(self, carte):
        self.cartes.append(carte)

    def sauvegarder(self, conn):
        with conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO decks (nom, couleurs, leader)
                VALUES (?, ?, ?);
            """, (self.nom, ','.join(self.couleurs), self.leader.nom))
            self.id = cur.lastrowid  # Mise à jour de l'id après l'insertion

            for carte in self.cartes:
                id_carte = carte.sauvegarder(conn)
                cur.execute("""
                    INSERT INTO cartes_decks (id_carte, id_deck)
                    VALUES (?, ?);
                """, (id_carte, self.id))

    def supprimerCarte(self, carte, conn):
        if carte in self.cartes:
            self.cartes.remove(carte)
            with conn:
                conn.execute("""
                    DELETE FROM cartes_decks WHERE id_carte = ? AND id_deck = ?;
                """, (carte.id, self.id))
                
