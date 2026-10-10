# Terraform : phase 1 (état distant + réseau)

Ordre d'exécution (détails dans le guide du document) :

1. `bootstrap/` : crée le bucket S3 qui stocke l'état. À faire UNE SEULE FOIS. Ne jamais détruire.
2. `envs/dev/` : crée le réseau (VPC) en utilisant le bucket comme backend. À détruire après chaque session.

```
bootstrap/        bucket S3 (état local, exécuté une fois)
modules/vpc/      module réutilisable : VPC, sous-réseaux, IGW, NAT, routes
envs/dev/         environnement dev : appelle le module, état distant dans S3
```
