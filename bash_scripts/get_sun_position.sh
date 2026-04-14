#!/bin/bash

year=2026
outdir=/users/dbautist/CHIME_landing_directory/sunPosition/

for month in {1..12}; 
    do for day in {1..31}; 
        do python3 ../chime/get_sun_position.py $day $month $year -o $outdir ; 
    done ; 
done
