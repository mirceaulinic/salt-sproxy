VERSION ?= 2019.2.0
IMAGE ?= mirceaulinic/salt-sproxy
TAG ?= $(IMAGE):$(VERSION)

build%:
	docker build -f Dockerfile$(@:-build=) . -t $(TAG) --build-arg SALT_VERSION=$(VERSION)
