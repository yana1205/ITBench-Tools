# Makefile to run Ansible playbooks

help:
	@echo "Makefile commands:"
	@echo "deploy_bundle -- [onetime] deploys the bundle to the cluster"
	@echo "inject_fault -- [onetime] define a new policy (policies) and enable fault for an compliance violation"
	@echo "destroy_bundle -- [onetime] destroy the target environment"
	@echo "help   - Display this help information"


deploy_bundle:
	ansible-playbook ./playbooks/deploy.yml

inject_fault:
	ansible-playbook ./playbooks/execute.yml

destroy_bundle:
	ansible-playbook playbooks/destroy.yml

evaluate:
	ansible-playbook playbooks/eval.yml