output "secret_arn" {
  description = "ARN du secret (identifiant unique AWS)"
  value       = aws_secretsmanager_secret.db.arn
}

output "secret_name" {
  description = "Nom du secret"
  value       = aws_secretsmanager_secret.db.name
}