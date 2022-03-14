fetch:
	./get_daily_jzqc_stats.sh
	rm -f data/JZQC.csv
	cat data/header data/*.csv > JZQC.csv