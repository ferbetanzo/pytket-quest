import pyquest
from pyquest import Register, Circuit
from pyquest.unitaries import H
from mpi4py import MPI


def main() -> int:
    mpi_comm = MPI.COMM_WORLD
    mpi_rank = mpi_comm.Get_rank()
    mpi_size = mpi_comm.Get_size()

    print(pyquest.env)
    print(f"Rank: {mpi_rank}, Size: {mpi_size} running on {MPI.Get_processor_name()}")

    num_qubits = 16
    reg = Register(num_qubits)
    h_gates = [H(i) for i in range(num_qubits)]
    circ = Circuit(h_gates)
    reg.apply_circuit(circ)

    result = reg.prob_of_all_outcomes([i for i in range(num_qubits)])

    # The process with rank 0 is often used as the root process in collective communications.
    if mpi_rank == 0:
        print(result)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
