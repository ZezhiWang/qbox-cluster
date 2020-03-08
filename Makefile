CREDENTIALS:=$$(cat values.tfvars | grep service_account_key_path | cut -d "\"" -f 2)

build:
	GOOGLE_APPLICATION_CREDENTIALS=$(CREDENTIALS) terraform init
	GOOGLE_APPLICATION_CREDENTIALS=$(CREDENTIALS) terraform apply -auto-approve -var-file="values.tfvars"

destroy:
	GOOGLE_APPLICATION_CREDENTIALS=$(CREDENTIALS) terraform destroy -auto-approve -var-file="values.tfvars"

show:
	GOOGLE_APPLICATION_CREDENTIALS=$(CREDENTIALS) terraform show
