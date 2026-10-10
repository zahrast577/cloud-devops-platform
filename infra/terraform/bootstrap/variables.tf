variable "region" {
  description = "Région AWS utilisée pour tout le projet"
  type        = string
  default     = "eu-west-3"
}

variable "project" {
  description = "Nom du projet, utilisé dans les noms et les tags"
  type        = string
  default     = "items-platform"
}
