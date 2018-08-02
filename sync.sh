#!/bin/sh

echo "Running Gitbook Build"
gitbook build src/

echo "Syncing Files"
rsync -avzP src/_book/* root@zek.hydr0.com:/var/www/rowboat-docs/
