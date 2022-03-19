default: fetch csv

fetch:
	./get_daily_jzqc_stats.sh

csv:
	rm -f data/JZQC.csv
	cat data/header data/*.csv > JZQC.csv
	cp JZQC.csv /mnt/c/Users/patrickl/Downloads/