locals {
  name = "${var.project}-${var.environment}"
}

module "vpc" {
  source = "../../modules/vpc"

  name               = local.name
  cluster_name       = local.name
  cidr               = var.vpc_cidr
  az_count           = 2
  single_nat_gateway = var.single_nat_gateway
}
module "ecr" {
  source = "../../modules/ecr"

  repository_names = ["items-api", "items-frontend"]
  force_delete     = true
}
