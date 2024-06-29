## How to run distributed calculations locally?
These instructions will guide you through the process of running distributed calculations locally using Docker and Open MPI. Distributed calculations allow you to perform complex computations across multiple nodes, which can significantly improve performance for large datasets.

### Instructions
1. Build Docker image of `pytket-quest` package.
2. Build Docker image of `pyQuEST` package with support of distributed calculations.
3. Build Docker image with `rshd` service and installed packages from the previous steps as well as Open MPI(`mpi4py`).

Let's start from the step 1. Inside `pytket-quest` directory run.

```
$> docker build -f Dockerfile -t pytketquest .
```

This command builds a Docker image using the Dockerfile in the current directory and tags it as `pytketquest`.

2. For convenience step 2 and 3 were merged with the step 1 in a single multi-stage Docker build [Dockerfile](./Dockerfile). Run the following commands:

```
$> cd ./tests/distributed
$> docker compose -p pytketquest -f docker-compose.yml up --build --scale mpi_node=4 -d
```

Alternatively, you can run [run-docker-compose.sh](./run-docker-compose.sh) script with the number of nodes as an argument:

```
$> ./run-docker-compose.sh -n 4
```

where `-n 4` corresponds to number of nodes over which we want to distribute our calculations.

3. Run the following command, replacing <container_id> with the ID of the root or master container and <ip_addresses> with the IP addresses of the 4 containers:

```
$> docker exec --user mpirun -i <container_id> mpirun \
    --mca btl tcp,self \
    --mca plm_rsh_no_tree_spawn 1 \
    --mca btl_tcp_if_include eth0 \
    --mca plm_rsh_agent rsh \
    --host <ip_addresses> \
    -np 4 python test_pytketquest.py
```

Alternatively, you can run the [run-mpirun.sh](./run-mpirun.sh) script:
```
$> ./run-mpirun.sh
```

After running the distributed calculations, you can stop and remove the Docker containers with the following command:

```
$> docker compose -p pytketquest down
```