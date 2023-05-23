PROJECT_NAME=ktransv2
DOCKERHUB_USERNAME=johannes89
VERSION = 1

clear:

	docker stop ${PROJECT_NAME}
	docker rm ${PROJECT_NAME}
	docker rmi ${PROJECT_NAME}

build:

	rm -r transformers || true
	cp -r ../src/transformers .
	docker stop ${PROJECT_NAME} || true && docker rm ${PROJECT_NAME} || true
	docker build -t ${PROJECT_NAME} .
	docker run -dt --name ${PROJECT_NAME} -p 9123:8080 -v ${PWD}/../:/workspace ${PROJECT_NAME} sleep infinity

enter:

	docker exec -it ${PROJECT_NAME}  /bin/bash


push:

	echo "Pushing ${PROJECT_NAME} to dockerhub" with version ${VERSION}
	
	docker tag ${PROJECT_NAME} ${DOCKERHUB_USERNAME}/${PROJECT_NAME}:${VERSION}

	docker push ${DOCKERHUB_USERNAME}/${PROJECT_NAME}:${VERSION}

	echo "Pushed: ${DOCKERHUB_USERNAME}/${PROJECT_NAME}:${VERSION}"


