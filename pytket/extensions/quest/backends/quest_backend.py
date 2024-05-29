# Copyright 2019-2024 Quantinuum
#s
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

from typing import List, Sequence, Optional, Type, Union,  cast
from logging import warning
from random import Random
from pytket.backends import (
    Backend,
    CircuitStatus,
    ResultHandle,
)
from pytket.backends.resulthandle import _ResultIdTuple
from pytket.backends.backendinfo import BackendInfo
from pytket.backends.backendresult import BackendResult
from pytket.circuit import Circuit, OpType
from pytket.extensions.qulacs._metadata import __extension_version__
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
from quest_convert import (
    tk_to_quest,
    _IBM_GATES,
    _MEASURE_GATES,
    _ONE_QUBIT_GATES,
    _TWO_QUBIT_GATES,
    _ONE_QUBIT_ROTATIONS,
)

from pyquest import  QuESTEnvironment, Register
from pyquest.unitaries import *

_1Q_GATES = (
    set(_ONE_QUBIT_ROTATIONS)
    | set(_ONE_QUBIT_GATES)
    | set(_MEASURE_GATES)
    | set(_IBM_GATES)
)

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
        Backend for running simulations on the pyQuest simulator

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
        if result_type == "state_vector":
            self._sim = Register
        elif result_type == "density_matrix":
            self._sim = Register
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

    @property
    def _result_id_type(
        self,
    ) -> _ResultIdTuple:
        raise NotImplementedError

    def process_circuits(
        self,
        circuits: Sequence[Circuit],
        n_shots: int | Sequence[int] | None = None,
        valid_check: bool = True,
        **kwargs: int | float | str | None
    ) -> List[ResultHandle]:
        circuits = list(circuits)

        if valid_check:
            self._check_all_circuits(circuits, nomeasure_warn=False)

        seed = cast(Optional[int], kwargs.get("seed"))
        rng = Random(seed) if seed else None
        raise NotImplementedError

    def circuit_status(self, handle: ResultHandle) -> CircuitStatus:
        raise NotImplementedError
