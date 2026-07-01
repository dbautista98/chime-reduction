#!/bin/bash

foo=$(pip freeze | grep chime 2> /dev/null)

if [ $? == 1 ] ; then 
    echo chime package not installed
else
    echo chime package successfully installed
fi
