PROJECT_NAME=kserve_transformers

clear:

	docker stop ${PROJECT_NAME}
	docker rm ${PROJECT_NAME}
	docker rmi ${PROJECT_NAME}

build:

	rm -r transformers || true
	cp -r ../src/transformers .
	docker stop ${PROJECT_NAME} || true && docker rm ${PROJECT_NAME} || true
	docker build -t ${PROJECT_NAME} .
	docker run -dt --name ${PROJECT_NAME} -p 9123:8080 ${PROJECT_NAME} sleep infinity

enter:

	docker exec -it ${PROJECT_NAME}  /bin/bash

