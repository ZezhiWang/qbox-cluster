provider "google-beta" {

  project = "ordinal-motif-270122"
  credentials = file(var.service_account_key_path)
  region  = "us-central1"
  zone    = "us-central1-c"

}

resource "google_container_cluster" "primary" {

  provider = google-beta
  name               = "primary"
  initial_node_count = 3

  node_config {
    machine_type = "n1-standard-2"
    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
    ]
  }

  master_auth {
    username = "admin"
    password = var.password
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  addons_config {
    istio_config {
      disabled = "false"
    }
  }

}

output "cluster_name" {
  value = google_container_cluster.primary.name
}


output "cluster_zone" {
  value = google_container_cluster.primary.zone
}