VERSION ?= $(shell git describe --tags --always --dirty="-dev")
SALT_VERSION ?= 2019.2.0
IMAGE ?= mirceaulinic/salt-sproxy
TAG ?= $(IMAGE):$(VERSION)

release:
	rm -rf dist
	python setup.py sdist
	python3 setup.py sdist
	twine upload dist/* --skip

docker-build%:
	docker build -f Dockerfile$($(@:build.o=):build=) . -t $(TAG) --build-arg SALT_VERSION=$(SALT_VERSION)

test:
	echo 'Test'
