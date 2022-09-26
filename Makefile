install-docker:
	sh ./first_project/src/sh/install_docker.sh

build:
	docker build . -t thooper-linux-local

shell: build
	sh ./first_project/src/sh/shell.sh

tf-notebooks:
	jupyter notebook