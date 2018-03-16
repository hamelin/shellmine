IMAGE=$(or ${SHELLMINE_IMAGE},shell-mining)
CONTAINER=$(or ${SHELLMINE_CONTAINER},shell-mining)
VOLUME_DB=$(or ${SHELLMINE_DB},$$HOME/.shell-mining)

.PHONY: build
build:
	docker build -t "$(IMAGE)" .

run:
	mkdir -p "$(VOLUME_DB)"
	docker run --rm --detach \
		--name "$(CONTAINER)" \
		--volume "$(VOLUME_DB):/var/lib/postgresql/data" \
		"$(IMAGE)"

attach:
	docker inspect "$(CONTAINER)" >/dev/null 2>&1 && docker attach "$(CONTAINER)"

detach:
	docker inspect "$(CONTAINER)" >/dev/null 2>&1 && pkill -f 'docker.*attach'

kill:
	docker inspect "$(CONTAINER)" >/dev/null 2>&1 && docker kill "$(CONTAINER)"

.PHONY: install
install: build
	echo "UNIMPLEMENTED YET" && exit 1
