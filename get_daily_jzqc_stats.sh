#!/bin/bash

DATE=$(date -d yesterday +"%Y-%m-%d")
echo $DATE
python get_jzqc_stats.py $DATE > data/$DATE.csv