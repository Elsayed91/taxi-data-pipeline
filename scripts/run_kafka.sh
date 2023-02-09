#!/bin/bash
# Small quality of life script to easily deploy and destroy kafka
# Using without arguments will create the needed deployments
# to destroy simply run with --kill argument.
# it iterates over the files in the kafka manifests directory

DIRECTORY=components/kafka/manifests

if [ "$1" == "--kill" ]; then
    for file in $DIRECTORY/*; do
        echo "Deleting $file"
        kubectl delete -f $file
    done
else
    for file in $DIRECTORY/*; do
        echo "Applying $file"
        cat $file | envsubst | kubectl apply -f -
    done
fi
