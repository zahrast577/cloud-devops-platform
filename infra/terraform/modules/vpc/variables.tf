variable "name" {
  description = "Préfixe utilisé pour nommer toutes les ressources réseau"
  type        = string
}

variable "cluster_name" {
  description = "Nom du futur cluster EKS (sert aux tags que EKS recherche sur les sous-réseaux)"
  type        = string
}

variable "cidr" {
  description = "Plage d'adresses IP du VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Nombre de zones de disponibilité utilisées (2 ou 3)"
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "az_count doit valoir 2 ou 3 (haute disponibilité)."
  }
}

variable "single_nat_gateway" {
  description = "true : une seule NAT Gateway (économique, pour dev). false : une par zone (haute disponibilité, pour prod)."
  type        = bool
  default     = true
}
