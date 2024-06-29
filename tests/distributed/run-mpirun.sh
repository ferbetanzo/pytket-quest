#!/bin/bash

project_name="pytketquest"

# Get the names of the running containers
containers=($(docker ps --format '{{.Names}}' --filter "name=$project_name*"))

ips=()
for container in "${containers[@]}"
do
    if [[ $container == $project_name* ]]; then
        # Get the IP address of the container
        ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $container)
        echo "Container $container IP: $ip"
        ips+=("$ip")
    fi
done

hosts=$(IFS=,; echo "${ips[*]}")
echo "Hosts: $hosts"
echo "Root node: ${containers[0]}"
echo "Number of nodes: ${#containers[@]}"

# The --mca btl tcp,self value tells MPI to use the TCP protocol for inter-node communication and the self protocol for intra-node communication.
docker exec --user mpirun -i ${containers[0]} mpirun \
    --mca btl tcp,self \
    --mca plm_rsh_no_tree_spawn 1 \
    --mca btl_tcp_if_include eth0 \
    --mca plm_rsh_agent rsh \
    --host $hosts \
    -np ${#containers[@]} python test_pytketquest.py
