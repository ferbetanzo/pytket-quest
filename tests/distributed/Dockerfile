# Build pyQuEST from source code with distributed mode enabled
FROM python:3.10-slim

RUN apt-get update && \
    # Install build tools
    apt-get install -y build-essential cmake && \
    # Install dependencies
    apt-get install -y git sed libblis-dev liblapack-dev libopenblas-dev gfortran && \
    apt-get install -y libopenmpi-dev && \
    apt-get clean && apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN git clone -b develop --recursive https://github.com/rrmeister/pyQuEST

WORKDIR /pyQuEST/

# Replace 'distributed': False with 'distributed': True in setup.py
RUN sed -i "s/'distributed': False/'distributed': True/g" setup.py

# Update the version of numpy in the build_requirements.txt file to use in Python 3.10
RUN sed -i 's/numpy==1.20.1/numpy==1.26.4/' build_requirements.txt

# Install the required Python packages specified in the build_requirements.txt file
RUN pip3 install --no-cache-dir -r build_requirements.txt

# Build the Python wheel package in /pyQuEST/dist/pyquest-0.0.1-cp39-cp39-linux_x86_64.whl using setup.py.
RUN python3 setup.py bdist_wheel

# Contains wheel file of pytketquest package.
FROM pytketquest

# Install mpi4py, pyQuEST from the wheel file and setup rsh daemon
FROM python:3.10-slim

# Some packages may have post-installation scripts that require interactive configuration or input from the user.
# This command can help to ensure that these prompts are automatically answered with their default values,
# allowing the installation process to proceed without any user interaction.
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    # Install dependencies and build tools
    apt-get install -y python3-dev python3-pip build-essential \
    xinetd rsh-redone-client rsh-redone-server \
    # Install Open MPI sources
    libopenmpi-dev && \
    apt-get clean && apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app/

COPY --from=0 /pyQuEST/dist/*.whl .
COPY --from=1 /app/dist/*.whl ./

RUN pip3 install numpy==1.26.4 mpi4py *.whl

# Set MPIRUN_USER as an environment variable
ENV MPIRUN_USER mpirun

# The -m option in the useradd command stands for "create home directory".
# The home directory is typically located at /home/mpirun
RUN useradd -m $MPIRUN_USER

# Create a symbolic link from python3 to python to run mpirun with python *.py or python3 *.py
RUN ln -s $(which python3) /usr/bin/python

COPY ./test_pyquest.py .
COPY ./test_pytketquest.py .

# Allow all hosts to access the container by modifying the /etc/hosts.allow file
# Deny all hosts from accessing the container by modifying the /etc/hosts.deny file
RUN echo "ALL: ALL" > /etc/hosts.allow && \
    echo "ALL: ALL" > /etc/hosts.deny

# Set up remote shell access configuration
# "+ +" means any user from any host is allowed to remotely log in without providing a password
RUN echo "+ +" > /home/$MPIRUN_USER/.rhosts && \
    chmod 600 /home/$MPIRUN_USER/.rhosts && \
    chown $MPIRUN_USER:$MPIRUN_USER /home/$MPIRUN_USER/.rhosts

# This configuration is used to enable the rsh (remote shell) service on the Docker container.
# We ensure that the service is properly configured and can be accessed remotely.
COPY ./rsh.xinetd /etc/xinetd.d/rsh

CMD ["/usr/sbin/xinetd", "-dontfork"]