import pydantic

from classiq.interface.generator.chemistry_function_params import (
    ChemistryFunctionParams,
)


class HVA(ChemistryFunctionParams):
    """
    Hamiltonian Variational Ansatz
    """

    reps: pydantic.PositiveInt = pydantic.Field(
        default=1, description="Number of layers in the Ansatz"
    )
    use_naive_evolution: bool = pydantic.Field(
        default=False, description="Whether to evolve the operator naively"
    )
    parameter_prefix: str = pydantic.Field(
        default="hva_param_",
        description="Prefix for the generated parameters",
    )
