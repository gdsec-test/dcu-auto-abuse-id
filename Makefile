REPONAME=infosec-dcu/auto_abuse_id
BUILDROOT=$(HOME)/dockerbuild/$(REPONAME)
DOCKERREPO=artifactory.secureserver.net:10014/docker-dcu-local/auto_abuse_id
DATE=$(shell date)

# libraries we need to stage for pip to install inside Docker build
PRIVATE_PIPS=git@github.secureserver.net:ITSecurity/blindAl.git \
git@github.secureserver.net:ITSecurity/dcdatabase.git

.PHONY: prep dev stage prod ote clean prod-deploy ote-deploy dev-deploy

all: prep dev

prep:
	@echo "----- preparing $(REPONAME) build -----"
	# stage pips we will need to install in Docker build
	mkdir -p $(BUILDROOT)/private_pips && rm -rf $(BUILDROOT)/private_pips/*
	for entry in $(PRIVATE_PIPS) ; do \
		cd $(BUILDROOT)/private_pips && git clone $$entry ; \
	done

	# copy the app code to the build root
	cp -rp ./* $(BUILDROOT)

stage: prep
	@echo "----- building $(REPONAME) stage -----"
	DOCKERTAG=stage
	docker build -t $(DOCKERREPO):stage $(BUILDROOT)

prod: prep
	@echo "----- building $(REPONAME) prod -----"
	sed -ie 's/THIS_STRING_IS_REPLACED_DURING_BUILD/$(DATE)/g' $(BUILDROOT)/k8s/prod/auto_abuse_id.deployment.yml
	docker build -t $(DOCKERREPO):prod $(BUILDROOT)

ote: prep
	@echo "----- building $(REPONAME) ote -----"
	sed -ie 's/THIS_STRING_IS_REPLACED_DURING_BUILD/$(DATE)/g' $(BUILDROOT)/k8s/ote/auto_abuse_id.deployment.yml
	docker build -t $(DOCKERREPO):ote $(BUILDROOT)

dev: prep
	@echo "----- building $(REPONAME) dev -----"
	sed -ie 's/THIS_STRING_IS_REPLACED_DURING_BUILD/$(DATE)/g' $(BUILDROOT)/k8s/dev/auto_abuse_id.deployment.yml
	docker build -t $(DOCKERREPO):dev $(BUILDROOT)

prod-deploy: prod
	@echo "----- deploying $(REPONAME) prod -----"
	docker push $(DOCKERREPO):prod
	kubectl --context prod apply -f $(BUILDROOT)/k8s/prod/auto_abuse_id.deployment.yml --record

ote-deploy: ote
	@echo "----- deploying $(REPONAME) ote -----"
	docker push $(DOCKERREPO):ote
	kubectl --context ote apply -f $(BUILDROOT)/k8s/ote/auto_abuse_id.deployment.yml --record

dev-deploy: dev
	@echo "----- deploying $(REPONAME) dev -----"
	docker push $(DOCKERREPO):dev
	kubectl --context dev apply -f $(BUILDROOT)/k8s/dev/auto_abuse_id.deployment.yml --record

clean:
	@echo "----- cleaning $(REPONAME) app -----"
	rm -rf $(BUILDROOT)
