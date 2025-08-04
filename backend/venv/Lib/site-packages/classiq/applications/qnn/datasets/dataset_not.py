from classiq.interface.exceptions import ClassiqIndexError

from classiq.applications.qnn.datasets.dataset_base_classes import MyDataset
from classiq.applications.qnn.datasets.datasets_utils import (
    all_bits_to_one,
    all_bits_to_zero,
)
from classiq.applications.qnn.types import DataAndLabel


class DatasetNot(MyDataset):
    def __len__(self) -> int:
        return 2

    def _get_data_and_label(self, index: int) -> DataAndLabel:
        if index == 0:
            data = all_bits_to_zero(self._n)
            label = all_bits_to_one(self._n)
        elif index == 1:
            data = all_bits_to_one(self._n)
            label = all_bits_to_zero(self._n)
        else:
            raise ClassiqIndexError(f"{self.__class__.__name__} out of range")

        return [data], label
