import pydantic

from classiq.interface.generator.arith.register_user_input import RegisterUserInput
from classiq.interface.generator.function_params import FunctionParams
from classiq.interface.helpers.custom_pydantic_types import PydanticProbabilityFloat

IN_NAME: str = "IN"
OUT_NAME: str = "OUT"


class Entangler(FunctionParams):
    """
    A Father class for all entangler classes
    """

    qubit_count: pydantic.PositiveInt = pydantic.Field(
        description="The number of qubits for the entangler."
    )
    schmidt_rank: pydantic.NonNegativeInt = pydantic.Field(
        default=0, description="The required schmidt rank (log of schmidt number)."
    )

    def _create_ios(self) -> None:
        self._inputs = {IN_NAME: RegisterUserInput(name=IN_NAME, size=self.qubit_count)}
        self._outputs = {
            OUT_NAME: RegisterUserInput(name=OUT_NAME, size=self.qubit_count)
        }


class TwoDimensionalEntangler(Entangler):
    """
    Creates a two dimensional cluster state with the specified number of qubits and schmidt rank
    (log of schmidt number). When the desired schmidt rank is too high, a rectangular grid with schmidt rank
    floor(sqrt(qubit_count))-1 is generated.
    """

    pass


class HypercubeEntangler(Entangler):
    """
    Creates a cluster/graph state in the form of a hypercube with the specified number of qubits. The hypercube is
    constructed by building cubes of growing dimension therefore if the number of qubits is not a a power of 2 (n=2^k)
    the last cube will not be completed. for example if n = 11 = 2^3 + 3 a three dimensional cube is constructed
    connected to additional 3 qubits in the natural order
    (that is, these qubits will be: 1000, 1001, 1010)
    """

    pass


class GridEntangler(Entangler):
    """
    creates a graph state in the form of multi-dimensional grid according to the specified number of qubits and Schmidt
    rank. If possible the grid will include the exact Schmidt rank if not a smaller grid with a lower schmidt rank is
    constructed - as close as possible to the specified parameters. if the specified Schmidt rank is too high a 'long'
    grid with the maximal possible Schmidt rank width is constructed (that still obeys the condition that the largest
    dimension minus 1 is larger then the sum of the (d_i - 1) -- d_i including all other dimensions)
    """

    grid_randomization: bool = pydantic.Field(
        default=True,
        description="Boolean determining whether the grid structure is randomly selected out of all grids which provide"
        "the same Schmidt rank width. If False the grid with maximal number of dimensions is selected.",
    )

    filling_factor: PydanticProbabilityFloat = pydantic.Field(
        default=1,
        description="float determining the fraction of cz gates that are included in a circuit for a given grid "
        "structure. For example, for filling_factor=0.5 half of the cz gates required for the full grid structure are "
        "included in the output circuit. The cz gates included in the circuit are chosen randomaly.",
    )
