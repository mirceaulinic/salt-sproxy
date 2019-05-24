VERSION ?= $(shell git describe --tags --always --dirty="-dev")
SALT_VERSION ?= 2019.2.0
IMAGE ?= mirceaulinic/salt-sproxy
TAG ?= $(IMAGE):$(VERSION)

publish:
	rm -rf dist
	python3 setup.py sdist
	twine upload dist/*

docker-build%:
	docker build -f Dockerfile$($(@:build.o=):build=) . -t $(TAG) --build-arg SALT_VERSION=$(SALT_VERSION)

test:
	echo 'Test'
