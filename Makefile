default: daily csv

DATE=$(shell date -d yesterday +"%Y-%m-%d")

daily:
	./get_daily_jzqc_stats.sh $(DATE)

csv:
	cat data/header data/*.csv | grep -v '^#' > JZQC.csv
	cp JZQC.csv /mnt/c/Users/patrickl/Downloads/
