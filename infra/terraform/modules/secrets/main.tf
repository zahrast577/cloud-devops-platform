# 1. Le mot de passe, généré aléatoirement par Terraform
resource "random_password" "db" {
  length  = var.password_length
  special = false
}

# 2. Le secret : le « coffre » dans Secrets Manager
resource "aws_secretsmanager_secret" "db" {
  name                    = var.name
  description             = "Identifiants de la base de données (${var.name})"
  recovery_window_in_days = var.recovery_window_in_days
  tags                    = var.tags
}

# 3. La version du secret : son contenu actuel, au format JSON
resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id

  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db.result
    dbname   = var.db_name
  })
}