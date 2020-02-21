
docker_auth:
	echo "$$DOCKER_PASSWORD" | docker login -u "$$DOCKER_USERNAME" --password-stdin

docker_build:
	docker build . --target app -t "openedx/edx-platform:latest"
	docker build . --target app -t "openedx/edx-platform:$$TRAVIS_COMMIT"
	docker build . --target newrelic -t "openedx/edx-platform:latest-newrelic"
	docker build . --target newrelic -t "openedx/edx-platform:$$TRAVIS_COMMIT-newrelic"

docker_push: docker_build docker_auth ## push to docker hub
	docker push "openedx/edx-platform:latest"
	docker push "openedx/edx-platform:$$TRAVIS_COMMIT"
	docker push "openedx/edx-platform:latest-newrelic"
	docker push "openedx/edx-platform:$$TRAVIS_COMMIT-newrelic"

