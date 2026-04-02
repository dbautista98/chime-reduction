#!/bin/bash

for year in {2024..2026}; 
    do for month in {01..12};
        do  for day in {01..31}; 
            do echo python3 ../chime/get_learmonth_data.py $day $month $year -o ../learmonthData/ ;
            python3 ../chime/get_learmonth_data.py $day $month $year -o ../learmonthData/ || echo "no data for this day" ; 
        done; 
    done;
done 
