# Copyright 2019-2024 Quantinuum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Methods to allow tket circuits to be ran on the QuEST simulator
"""

from typing import List, Sequence, Optional, Type, Union, Any
from logging import warning
from uuid import uuid4
import numpy as np
from pyquest import Register

from pytket.backends import (
    Backend,
    CircuitNotRunError,
    CircuitStatus,
    ResultHandle,
    StatusEnum,
)
from pytket.backends.resulthandle import _ResultIdTuple
from pytket.backends.backendinfo import BackendInfo
from pytket.backends.backendresult import BackendResult
from pytket.circuit import Circuit, OpType
from pytket.extensions.quest._metadata import __extension_version__
from pytket.passes import (
    BasePass,
    SynthesiseTket,
    SequencePass,
    DecomposeBoxes,
    FullPeepholeOptimise,
    FlattenRegisters,
    auto_rebase_pass,
)
from pytket.predicates import (
    GateSetPredicate,
    NoClassicalControlPredicate,
    NoFastFeedforwardPredicate,
    NoMidMeasurePredicate,
    NoSymbolsPredicate,
    DefaultRegisterPredicate,
    Predicate,
)

from pytket.extensions.quest.quest_convert import (
    tk_to_quest,
    _MEASURE_GATES,
    _ONE_QUBIT_GATES,
    _TWO_QUBIT_GATES,
    _ONE_QUBIT_ROTATIONS,
)

_1Q_GATES = set(_ONE_QUBIT_ROTATIONS) | set(_ONE_QUBIT_GATES) | set(_MEASURE_GATES)


class QuESTBackend(Backend):
    """
    Backend for running simulations on the QuEST simulator
    """

    _supports_shots = False
    _supports_counts = False
    _supports_state = True
    _supports_unitary = False
    _supports_density_matrix = True
    _supports_expectation = False
    _expectation_allows_nonhermitian = False
    _supports_contextual_optimisation = False
    _persistent_handles = False
    _GATE_SET = {
        *_TWO_QUBIT_GATES.keys(),
        *_1Q_GATES,
        OpType.Barrier,
    }

    def __init__(
        self,
        result_type: str = "state_vector",
    ) -> None:
        """
        Backend for running simulations on the QuEST simulator

        :param result_type: Indicating the type of the simulation result
            to be returned. It can be either "state_vector" or "density_matrix".
            Defaults to "state_vector"
        """
        super().__init__()
        self._backend_info = BackendInfo(
            type(self).__name__,
            None,
            __extension_version__,
            None,
            self._GATE_SET,
        )
        self._result_type = result_type
        self._sim: Type[Union[Register]]
        self._sim = Register
        if result_type == "state_vector":
            self._density_matrix = False
            self._supports_density_matrix = False
        elif result_type == "density_matrix":
            self._density_matrix = True
            self._supports_state = False
            self._supports_density_matrix = True
        else:
            raise ValueError(f"Unsupported result type {result_type}")

    @property
    def _result_id_type(self) -> _ResultIdTuple:
        return (str,)

    @property
    def backend_info(self) -> Optional["BackendInfo"]:
        return self._backend_info

    @property
    def required_predicates(self) -> List[Predicate]:
        return [
            NoClassicalControlPredicate(),
            NoFastFeedforwardPredicate(),
            NoMidMeasurePredicate(),
            NoSymbolsPredicate(),
            GateSetPredicate(self._GATE_SET),
            DefaultRegisterPredicate(),
        ]

    def rebase_pass(self) -> BasePass:
        return auto_rebase_pass(set(_TWO_QUBIT_GATES) | _1Q_GATES)

    def default_compilation_pass(self, optimisation_level: int = 1) -> BasePass:
        assert optimisation_level in range(3)
        if optimisation_level == 0:
            return SequencePass(
                [DecomposeBoxes(), FlattenRegisters(), self.rebase_pass()]
            )
        elif optimisation_level == 1:
            return SequencePass(
                [
                    DecomposeBoxes(),
                    FlattenRegisters(),
                    SynthesiseTket(),
                    self.rebase_pass(),
                ]
            )
        else:
            return SequencePass(
                [
                    DecomposeBoxes(),
                    FlattenRegisters(),
                    FullPeepholeOptimise(),
                    self.rebase_pass(),
                ]
            )

    def process_circuits(
        self,
        circuits: Sequence[Circuit],
        n_shots: int | Sequence[int] | None = None,
        valid_check: bool = True,
        **kwargs: int | float | str | None,
    ) -> List[ResultHandle]:
        circuits = list(circuits)

        if valid_check:
            self._check_all_circuits(circuits, nomeasure_warn=False)

        handle_list = []
        for circuit in circuits:
            quest_state = self._sim(circuit.n_qubits, self._density_matrix)
            quest_circ = tk_to_quest(
                circuit, reverse_index=True, replace_implicit_swaps=True
            )
            quest_state.apply_circuit(quest_circ)

            if self._result_type == "state_vector":
                state = quest_state[:]
            else:
                state = quest_state[:, :]
            qubits = sorted(circuit.qubits, reverse=False)

            if self._result_type == "state_vector":
                try:
                    phase = float(circuit.phase)
                    coeff = np.exp(phase * np.pi * 1j)
                    state *= coeff
                except TypeError:
                    warning(
                        "Global phase is dependent on a symbolic parameter, so cannot "
                        "adjust for phase"
                    )
            handle = ResultHandle(str(uuid4()))
            if self._result_type == "state_vector":
                self._cache[handle] = {
                    "result": BackendResult(state=state, q_bits=qubits)
                }
            else:
                self._cache[handle] = {
                    "result": BackendResult(density_matrix=state, q_bits=qubits)
                }

            handle_list.append(handle)
            del quest_state
            del quest_circ
        return handle_list

    def circuit_status(self, handle: ResultHandle) -> CircuitStatus:
        if handle in self._cache:
            return CircuitStatus(StatusEnum.COMPLETED)
        raise CircuitNotRunError(handle)

    def prob_of_all_outcomes(self, circuit: Circuit, qubits: List[int]) -> Any:
        quest_state = self._sim(circuit.n_qubits)
        quest_circ = tk_to_quest(circuit)
        quest_state.apply_circuit(quest_circ)
        return quest_state.prob_of_all_outcomes(qubits)
