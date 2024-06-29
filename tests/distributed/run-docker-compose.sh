#!/bin/bash

project_name="pytketquest"

docker compose -p $project_name down

# Default number of nodes
nodes=1

# Parse command-line options
while getopts ":n:" opt; do
  case ${opt} in
    n )
      nodes=$OPTARG
      ;;
    \? )
      echo "Invalid option: $OPTARG" 1>&2
      exit 1
      ;;
    : )
      echo "Invalid option: $OPTARG requires an argument" 1>&2
      exit 1
      ;;
  esac
done
shift $((OPTIND -1))

docker compose -p $project_name -f docker-compose.yml up --build --scale mpi_node=$nodes -d
