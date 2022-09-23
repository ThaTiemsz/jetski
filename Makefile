up:
	find /home/jetski/rowboat -name '*.pyc' -delete
	pm2 start start.yml

restart:
	pm2 restart all

stop:
	pm2 stop all

down:
	pm2 delete all

build:
	pm2 stop all
	pm2 delete all
	find /home/jetski/rowboat -name '*.pyc' -delete
	pm2 start start.yml

worker-logs:
	pm2 log worker

logs:
	pm2 log bot
