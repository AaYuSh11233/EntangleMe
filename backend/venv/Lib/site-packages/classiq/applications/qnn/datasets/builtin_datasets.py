from torch.utils.data import DataLoader
from torchvision.transforms import Lambda

from classiq.applications.qnn.datasets.dataset_not import DatasetNot
from classiq.applications.qnn.datasets.dataset_parity import DatasetSubsetParity
from classiq.applications.qnn.datasets.dataset_xor import DatasetXor
from classiq.applications.qnn.datasets.datasets_utils import (
    state_to_label,
    state_to_weights,
)

DATASET_NOT = DatasetNot(
    1, transform=Lambda(state_to_weights), target_transform=Lambda(state_to_label)
)
DATALOADER_NOT = DataLoader(DATASET_NOT, batch_size=2, shuffle=True)
DATASET_XOR = DatasetXor()
DATALOADER_XOR = DataLoader(DATASET_XOR, batch_size=4, shuffle=True)
DATASET_SUBSET_PARITY = DatasetSubsetParity(
    3,
    [0, 2],
    transform=Lambda(state_to_weights),
    target_transform=Lambda(state_to_label),
)
DATALOADER_SUBSET_PARITY = DataLoader(DATASET_SUBSET_PARITY, batch_size=8, shuffle=True)
