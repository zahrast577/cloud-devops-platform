variable "region" {
  description = "Région AWS (la même que dans bootstrap)"
  type        = string
  default     = "eu-west-3"
}

variable "project" {
  description = "Nom du projet"
  type        = string
  default     = "items-platform"
}

variable "environment" {
  description = "Nom de l'environnement"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "Plage d'adresses IP du VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "single_nat_gateway" {
  description = "Une seule NAT Gateway (économique) ou une par zone (haute disponibilité)"
  type        = bool
  default     = true
}
