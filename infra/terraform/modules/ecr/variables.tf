variable "repository_names" {
  description = "Noms des depots ECR a creer"
  type        = list(string)
}

variable "image_tag_mutability" {
  description = "IMMUTABLE (un tag ne peut pas etre ecrase) ou MUTABLE"
  type        = string
  default     = "IMMUTABLE"
}

variable "max_image_count" {
  description = "Nombre d'images conservees par depot"
  type        = number
  default     = 10
}

variable "force_delete" {
  description = "Permet de supprimer un depot meme s'il contient des images (utile en dev)"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags appliques aux depots"
  type        = map(string)
  default     = {}
}