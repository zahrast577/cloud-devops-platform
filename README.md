# Plateforme cloud-native sur AWS (Terraform, Ansible, Kubernetes, CI/CD)

Ce dépôt contient **l'application** (déjà prête) et l'emplacement de **la plateforme** que tu vas construire autour, étape par étape.

## Le rôle de l'application

L'application est la **charge utile** : ce que la plateforme construit, livre, fait tourner, surveille et protège. Tu ne la modifies pas pendant le projet. Elle est volontairement simple, mais elle contient exactement ce dont chaque outil DevOps a besoin pour être démontré :

| Ce que l'application fournit | Ce que ça permet de démontrer |
|---|---|
| 4 composants (frontend, API, PostgreSQL, Redis) | Un vrai déploiement multi-services sur Kubernetes |
| `GET /health` | Sonde de vie (livenessProbe) |
| `GET /ready` (vérifie PostgreSQL) | Sonde de disponibilité (readinessProbe) |
| `GET /metrics` | Scraping par Prometheus, dashboards Grafana |
| `GET /api/info` (nom du pod + version) | Voir le load balancing et les rollouts en direct |
| `GET /api/stress` (CPU borné) | Déclencher l'autoscaling (HPA) |
| Tests pytest | Étape « Test » des pipelines Jenkins et GitHub Actions |
| Dockerfiles multi-stage, non root | Étape « Build », scan Trivy |
| Configuration par variables d'environnement | ConfigMap et Secret Kubernetes |
| Cache Redis avec dégradation gracieuse | Comprendre pourquoi `/ready` ne dépend pas de Redis |

## Arborescence

```
.
├── app/
│   ├── api/                  API FastAPI (code, tests, Dockerfile)
│   └── frontend/             Interface React (Vite) + nginx + Dockerfile
├── docker-compose.yml        Lance toute l'application en local
├── .env.example              Modèle de configuration (à copier en .env)
├── Makefile                  Commandes du quotidien (make help)
├── scripts/
│   ├── smoke_test.sh         Test de fumée (utilisé par Jenkins plus tard)
│   └── load_test.py          Test de charge (étape autoscaling)
├── infra/terraform/          À écrire : étapes 3, 4, 5
├── infra/ansible/            À écrire : étape 6
├── k8s/                      À écrire : étapes 7, 10, 11, 12
├── ci/                       À écrire : Jenkinsfile (étape 8)
├── .github/workflows/        À écrire : CI GitHub Actions (étape 9)
└── docs/                     Schéma d'architecture, runbook, coûts
```

## Démarrage en local (étapes 1 et 2 du guide)

Prérequis : Docker avec Docker Compose.

```bash
make up          # crée .env au premier lancement, construit les images, démarre tout
```

- Application : http://localhost:8080
- Documentation de l'API : http://localhost:8000/docs
- Métriques Prometheus : http://localhost:8000/metrics

Ensuite :

```bash
make ps          # état des 4 services (tous "healthy")
make smoke       # test de fumée de bout en bout
make logs        # journaux
make down        # arrêt (les données sont conservées)
make clean       # arrêt + suppression des données
```

Tests unitaires de l'API (sans Docker) :

```bash
make test
```

## Les « contrats » à respecter pour les étapes suivantes

Ces valeurs sont déjà utilisées dans le code. Quand tu écriras Terraform, Kubernetes et Jenkins, reprends-les à l'identique, sinon rien ne se connectera.

| Élément | Valeur | Où tu l'utiliseras |
|---|---|---|
| Nom du Service de l'API | `api` | `k8s/` : nginx le contacte par `http://api:8000` |
| Port de l'API | `8000` | Service, Deployment, probes |
| Nom du Service du frontend | `frontend` | `k8s/` |
| Port du frontend | `8080` | Service, Deployment, probes |
| Sonde de vie de l'API | `GET /health` | `livenessProbe` |
| Sonde de disponibilité de l'API | `GET /ready` | `readinessProbe` |
| Sonde du frontend | `GET /healthz` | liveness et readiness |
| Métriques | `GET /metrics` sur le port 8000 | Prometheus |
| Dépôts ECR | `api` et `frontend` | Terraform (étape 5) |
| Variables de l'API | `DATABASE_URL`, `REDIS_HOST`, `REDIS_PORT`, `APP_VERSION` | ConfigMap et Secret |
| Version affichée | variable `APP_VERSION` | Jenkins y mettra le hash du commit |
| Utilisateurs des conteneurs | API : UID `10001` ; frontend : UID `101` | `securityContext` (non root) |

## Où l'application intervient dans chaque étape

| Étape du guide | Rôle de l'application |
|---|---|
| 1. Application minimale | Tu l'as : les fichiers sont fournis |
| 2. Docker et compose | Tu construis, lances, et tu étudies les Dockerfiles |
| 3, 4, 5. Terraform | Pas utilisée directement ; les dépôts ECR `api` et `frontend` lui sont destinés |
| 6. Ansible | Pas utilisée (tu configures les serveurs Jenkins et bastion) |
| 7. Kubernetes | Tu la déploies : manifests pour `frontend`, `api`, PostgreSQL, Redis |
| 8. Jenkins | La pipeline la teste, la construit, la pousse sur ECR et la déploie |
| 9. GitHub Actions | La CI teste son code et scanne son code, ses dépendances et ses images |
| 10. RBAC et réseau | Les NetworkPolicies reproduisent ses flux : frontend vers API, API vers PostgreSQL et Redis |
| 11. Supervision | Prometheus scrape `/metrics`, Grafana trace ses courbes |
| 12. Autoscaling | `/api/stress` génère la charge qui fait monter le nombre de pods |
| 13. Pannes | Tu casses ses pods, sa base, sa version, et tu observes |

## Limites connues (à mentionner dans ton README final, c'est un bon point)

- Les tables sont créées au démarrage de l'API. En production, on utiliserait des migrations (Alembic) lancées par un Job dédié.
- `/api/stress` est un outil de test : il ne doit pas être exposé en production.
- PostgreSQL dans Kubernetes est choisi pour l'apprentissage. En production réelle, on préférerait un service géré (RDS).
