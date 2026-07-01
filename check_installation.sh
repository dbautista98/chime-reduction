#!/bin/bash

foo=$(pip freeze | grep chime 2> /dev/null)

if [ $? == 0 ] ; then 
    echo chime package successfully installed
else
    echo chime package not installed
fi
