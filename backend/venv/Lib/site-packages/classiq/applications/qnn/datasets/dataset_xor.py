from classiq.applications.qnn.datasets.dataset_base_classes import MyDataset
from classiq.applications.qnn.types import DataAndLabel


class DatasetXor(MyDataset):
    def __len__(self) -> int:
        return 2**self._n

    def _get_data_and_label(self, index: int) -> DataAndLabel:
        bin_str = self._get_bin_str(index)
        data_value = map(int, bin_str)

        label_value = bin_str.count("1") % 2

        return list(data_value), int(label_value)
