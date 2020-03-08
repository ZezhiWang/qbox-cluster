# Deliberately kept insecure in that it only uses HTTP Basic Auth. 
# We should fix this eventually, but good enough for testing for now.
provider "kubectl" {
  load_config_file = "false"

  host = google_container_cluster.primary.endpoint

  username = google_container_cluster.primary.master_auth[0].username
  password = google_container_cluster.primary.master_auth[0].password
}

data "kubectl_file_documents" "manifests" {
    content = file(var.bookinfo_apps_path)
}

resource "kubectl_manifest" "test" {
    for_each = toset(data.kubectl_file_documents.manifests.documents)
    yaml_body = each.value
}