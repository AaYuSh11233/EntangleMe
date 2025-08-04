from typing import Literal, Optional, Union

from classiq.applications.qnn.datasets.dataset_base_classes import MySubsetDataset
from classiq.applications.qnn.types import DataAndLabel, Transform


class DatasetSubsetParity(MySubsetDataset):
    def __init__(
        self,
        n: int = 2,
        subset: Union[list[int], Literal["all"]] = "all",
        add_readout_qubit: bool = True,
        transform: Optional[Transform] = None,
        target_transform: Optional[Transform] = None,
    ) -> None:
        super().__init__(n, subset, transform, target_transform)

        self._add_readout_qubit = add_readout_qubit

    def __len__(self) -> int:
        return 2**self._n

    def _get_data_and_label(self, index: int) -> DataAndLabel:
        bin_str = self._get_bin_str(index)

        data = list(map(int, bin_str)) + [0] * self._add_readout_qubit

        label_value = self._get_subset(bin_str).count("1") % 2

        return data, int(label_value)


class DatasetParity(DatasetSubsetParity):
    def __init__(
        self,
        n: int = 2,
        add_readout_qubit: bool = True,
        transform: Optional[Transform] = None,
        target_transform: Optional[Transform] = None,
    ) -> None:
        super().__init__(n, "all", add_readout_qubit, transform, target_transform)
