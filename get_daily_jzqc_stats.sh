#!/bin/bash

DATE=$1
echo $DATE
python get_jzqc_stats.py $DATE > data/$DATE.csv
