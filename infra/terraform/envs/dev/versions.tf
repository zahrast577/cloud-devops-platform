terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Backend S3 « partiel » : les valeurs (nom du bucket...) viennent du fichier backend.hcl,
  # car un bloc backend n'accepte pas de variables.
  backend "s3" {}
}

provider "aws" {
  region = var.region

  # Ces tags sont ajoutés automatiquement à TOUTES les ressources créées.
  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
