#!/bin/bash
CUR_DIR=$(dirname $0)

if [[ "$1" == *.yaml ]]; then  
CONFIG=$1
shift
fi

$CUR_DIR/siteparser.py -c $CUR_DIR/${CONFIG:-siteparser.yaml} $*