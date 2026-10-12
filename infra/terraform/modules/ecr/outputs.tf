output "repository_urls" {
  description = "URL de chaque depot (adresse a utiliser dans docker push)"
  value       = { for name, repo in aws_ecr_repository.this : name => repo.repository_url }
}

output "repository_arns" {
  description = "ARN de chaque depot"
  value       = { for name, repo in aws_ecr_repository.this : name => repo.arn }
}