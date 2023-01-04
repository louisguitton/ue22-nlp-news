backfill:
	cd newsapi-crawl && python backfill.py 

run:
	docker-compose up

ingest:
	python -m station.management.es

kibana:
	open http://localhost:5601

front:
	cd searchkit-ui && yarn start

download-data:
	aws s3 sync s3://articles-louisguitton/newsapi data/newsapi
