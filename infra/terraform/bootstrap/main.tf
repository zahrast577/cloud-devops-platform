# Ce dossier crée UNIQUEMENT le bucket qui stockera l'état (state) de Terraform.
# Il a lui-même un état local : c'est le problème de « l'œuf et de la poule ».
# On l'exécute une seule fois, et on ne le détruit jamais.

data "aws_caller_identity" "current" {}

locals {
  # Un nom de bucket S3 doit être unique dans le monde entier :
  # on y ajoute l'identifiant du compte AWS pour éviter les collisions.
  bucket_name = "${var.project}-tfstate-${data.aws_caller_identity.current.account_id}-${var.region}"
}

resource "aws_s3_bucket" "tfstate" {
  bucket = local.bucket_name

  # Garde-fou : Terraform refuse de supprimer ce bucket, même par erreur.
  lifecycle {
    prevent_destroy = true
  }
}

# Versioning : chaque modification de l'état est conservée, on peut revenir en arrière.
resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Chiffrement au repos : l'état peut contenir des valeurs sensibles.
resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Interdit tout accès public au bucket.
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Supprime les très anciennes versions de l'état pour ne pas grossir indéfiniment.
resource "aws_s3_bucket_lifecycle_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    id     = "expire-old-state-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  depends_on = [aws_s3_bucket_versioning.tfstate]
}
