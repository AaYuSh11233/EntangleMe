from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Literal, Optional, TypeVar, Union

from torch import Tensor, tensor
from torch.utils.data import Dataset

from classiq.interface.exceptions import ClassiqIndexError, ClassiqValueError

from classiq.applications.qnn.types import DataAndLabel, Transform

T = TypeVar("T")


class MyDataset(Dataset, ABC):
    def __init__(
        self,
        n: int = 2,
        transform: Optional[Transform] = None,
        target_transform: Optional[Transform] = None,
    ) -> None:
        self._n = n
        self.transform = transform
        self.target_transform = target_transform

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def _get_data_and_label(self, index: int) -> DataAndLabel:
        pass

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor]:
        if index < 0 or index >= len(self):
            raise ClassiqIndexError(f"{self.__class__.__name__} out of range")

        the_data, the_label = self._get_data_and_label(index)

        data = tensor(the_data)
        if self.transform:
            data = self.transform(data)

        label = tensor(the_label)
        if self.target_transform:
            label = self.target_transform(label)

        return data.float(), label.float()

    def _get_bin_str(self, num: int) -> str:
        return bin(num)[2:].zfill(self._n)[::-1]


class MySubsetDataset(MyDataset, ABC):
    def __init__(
        self,
        n: int = 2,
        subset: Union[list[int], Literal["all"]] = "all",
        transform: Optional[Transform] = None,
        target_transform: Optional[Transform] = None,
    ) -> None:
        super().__init__(n, transform, target_transform)

        self._subset: Sequence[int]
        if isinstance(subset, list):
            if not all(0 <= i < n for i in subset):
                raise ClassiqValueError(
                    "Invalid subset indices. Make sure each index is between [0, n)"
                )
            self._subset = subset
        elif subset == "all":
            self._subset = range(n)
        else:
            raise ClassiqValueError(
                'Invalid subset - please enter a `list` of `int`, or the string "all"'
            )

    def _get_subset(self, coll: Sequence[T]) -> list[T]:
        return [coll[i] for i in self._subset]
