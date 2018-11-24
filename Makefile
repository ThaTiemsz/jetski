up:
	docker-compose up -d

restart:
	docker-compose restart

stop:
	docker-compose stop

down:
	docker-compose down

build:
	docker-compose up -d --no-deps --build

cli:
	docker-compose exec bot /bin/bash

worker-logs:
	docker-compose exec workers tail -F worker-0.log

logs:
	docker-compose logs -f --tail="1500" $(image)
