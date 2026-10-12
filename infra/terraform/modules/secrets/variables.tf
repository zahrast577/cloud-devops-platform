variable "name" {
  description = "Nom du secret dans Secrets Manager (ex. items-platform/dev/db)"
  type        = string
}

variable "db_username" {
  description = "Nom d'utilisateur de la base de données"
  type        = string
  default     = "items_admin"
}

variable "db_name" {
  description = "Nom de la base de données"
  type        = string
  default     = "items"
}

variable "password_length" {
  description = "Longueur du mot de passe généré"
  type        = number
  default     = 32
}

variable "recovery_window_in_days" {
  description = "Délai de récupération après suppression. 0 = suppression immédiate (laboratoire). En production : 7 à 30."
  type        = number
  default     = 0
}

variable "tags" {
  description = "Étiquettes appliquées au secret"
  type        = map(string)
  default     = {}
}