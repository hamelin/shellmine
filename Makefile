IMAGE=$(or ${SHELLMINE_IMAGE},shell-mining)
CONTAINER=$(or ${SHELLMINE_CONTAINER},shell-mining)
VOLUME_DB=$(or ${SHELLMINE_DB},$$HOME/.shell-mining)

.PHONY: build
build:
	docker build -t "$(IMAGE)" .

.PHONY: attach
attach:
	docker inspect "$(CONTAINER)" >/dev/null 2>&1 && docker attach "$(CONTAINER)"

.PHONY: detach
detach:
	docker inspect "$(CONTAINER)" >/dev/null 2>&1 && pkill -f 'docker.*attach'

.PHONY: kill
kill:
	docker inspect "$(CONTAINER)" >/dev/null 2>&1 && docker kill "$(CONTAINER)"

.PHONY: install
install: build
	echo "UNIMPLEMENTED YET" && exit 1
