output "bucket_name" {
  description = "Nom du bucket qui stocke l'état Terraform"
  value       = aws_s3_bucket.tfstate.id
}

output "backend_hcl" {
  description = "Contenu à copier dans envs/dev/backend.hcl"
  value       = <<-EOT
    bucket       = "${aws_s3_bucket.tfstate.id}"
    key          = "envs/dev/terraform.tfstate"
    region       = "${var.region}"
    encrypt      = true
    use_lockfile = true
  EOT
}
