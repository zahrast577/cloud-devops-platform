module "secrets" {
  source = "../../modules/secrets"

  name        = "items-platform/dev/db"
  db_username = "items_admin"
  db_name     = "items"

  # Laboratoire : suppression immédiate pour pouvoir détruire et recréer sans blocage.
  # En production, mettre 7 à 30.
  recovery_window_in_days = 0
}

output "db_secret_arn" {
  description = "ARN du secret de la base de données"
  value       = module.secrets.secret_arn
}

output "db_secret_name" {
  description = "Nom du secret de la base de données"
  value       = module.secrets.secret_name
}