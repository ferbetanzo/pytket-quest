import pyquest

from mpi4py import MPI

from pytket.circuit import Circuit, OpType
from pytket.extensions.quest import QuESTBackend


def main() -> int:
    mpi_comm = MPI.COMM_WORLD
    mpi_rank = mpi_comm.Get_rank()
    mpi_size = mpi_comm.Get_size()

    print(pyquest.env)
    print(f"Rank: {mpi_rank}, Size: {mpi_size} running on {MPI.Get_processor_name()}")

    num_qubits = 16
    backend = QuESTBackend()
    circ = Circuit(num_qubits)
    for i in range(num_qubits):
        circ.add_gate(OpType.H, [i])

    circ = backend.get_compiled_circuit(circ)
    backend.run_circuit(circ)

    result = backend.prob_of_all_outcomes(circ, [i for i in range(num_qubits)])

    # The process with rank 0 is often used as the root process in collective communications.
    if mpi_rank == 0:
        print(result)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
