# DRC - Dominion Rev Center
## Système de gestion des prêts d'équipements

### Installation

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Appliquer les migrations
python3 manage.py migrate

# 3. Créer un super utilisateur
python3 manage.py createsuperuser

# 4. Lancer le serveur
python3 manage.py runserver
```

### Structure du projet

```
RDC/
├── DRC/                  # Configuration Django
│   ├── settings.py       # Paramètres (MySQL, DRF, Auth)
│   ├── urls.py           # Routes principales
│   └── wsgi.py
├── core/                 # Application principale
│   ├── models.py         # User, Direction, Department, SubDepartment, Equipment, Movement
│   ├── serializers.py    # Sérialisation et validation
│   ├── views.py          # API et pages HTML
│   ├── urls.py           # Routes de l'app
│   └── admin.py          # Interface admin Django
├── templates/            # Pages HTML
│   ├── base.html         # Template de base
│   ├── login.html        # Page de connexion
│   ├── situation.html    # Dashboard (stock, prêts, historique)
│   ├── mouvement.html    # Formulaire de mouvements
│   ├── administration.html # Gestion utilisateurs/équipements/organisation
│   └── verify_email.html # Vérification email
├── static/
│   └── style.css         # Design system
├── manage.py
└── requirements.txt
```

### API Endpoints

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | `/api/login/` | Connexion |
| POST | `/api/logout/` | Déconnexion |
| GET | `/api/me/` | Utilisateur courant |
| GET/POST | `/api/users/` | Gestion utilisateurs (admin) |
| GET/POST | `/api/equipment/` | Gestion équipements |
| POST | `/api/movements/` | Créer un mouvement |
| GET | `/api/stock/` | Stock calculé |
| GET | `/api/loans/` | Prêts actifs |
| GET | `/api/history/` | Historique complet |
| GET | `/api/directions/` | Directions |
| GET | `/api/departments/` | Départements |

### Logique métier

- **ENTREE / RETOUR** → Stock augmente
- **PRET / SORTIE** → Stock diminue
- Stock négatif interdit
- Chaque mouvement enregistre: qui l'a fait, à qui, quel équipement, quantité, date
