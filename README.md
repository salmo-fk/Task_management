# Task Manager - Version Python CLI

Gestionnaire de tâches minimal développé avec approche TDD en utilisant pytest.

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

### Démarrer l'API
L’API sera accessible sur :
```bash
http://localhost:5000
```
```bash
python src/app.py --help
```
### Accéder à la documentation Swagger
Une fois le serveur lancé, ouvrez dans votre navigateur :
```bash
http://localhost:5000/docs
```
### Lancer les tests
```bash
# Tests simples
pytest

# Tests Tasks
pytest

# Tests Users
pytest  

# Tests avec couverture
pytest --cov=src --cov-report=html

# Tests en mode verbose
pytest -v

# Tests avec monitoring des modifications
pytest-watch
```

## Couverture de tests

Objectif : maintenir une couverture > 90% sur la logique métier.

```bash
pytest --cov=src --cov-report=term-missing
```
