output "vpc_id" {
  description = "Identifiant du VPC"
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "Identifiants des sous-réseaux publics"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Identifiants des sous-réseaux privés"
  value       = aws_subnet.private[*].id
}

output "nat_gateway_ids" {
  description = "Identifiants des NAT Gateways"
  value       = aws_nat_gateway.this[*].id
}
