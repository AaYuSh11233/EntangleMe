import pydantic


class SynthesisStepDurations(pydantic.BaseModel):
    preprocessing: float
    solving: float
    conversion_to_circuit: float
    postprocessing: float

    def total_time(self) -> float:
        return sum(
            time if time is not None else 0
            for time in (
                self.preprocessing,
                self.solving,
                self.conversion_to_circuit,
                self.postprocessing,
            )
        )
