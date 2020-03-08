build:
	GOOGLE_APPLICATION_CREDENTIALS=$$(cat values.tfvars | grep service_account_key_path | cut -d "\"" -f 2) terraform init
	GOOGLE_APPLICATION_CREDENTIALS=$$(cat values.tfvars | grep service_account_key_path | cut -d "\"" -f 2) terraform apply -var-file="values.tfvars"

destroy:
	GOOGLE_APPLICATION_CREDENTIALS=$$(cat values.tfvars | grep service_account_key_path | cut -d "\"" -f 2) terraform destroy -var-file="values.tfvars"