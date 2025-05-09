import torch
import torchvision
import torchvision.transforms as transforms
import torchvision.datasets as datasets 
import numpy as np
import random
from torch.utils.data import DataLoader, random_split, Subset

import dr_util.determinism_utils as dtu

DEFAULT_DOWNLOAD = True
DEFAULT_TRANSFORM = None

def get_cifar_dataset(
    dataset_name,
    source_split, # the official split (train or test)
    root,
    transform=DEFAULT_TRANSFORM,
    download=DEFAULT_DOWNLOAD,
):
    """
    Loads a specified dataset (CIFAR-10 or CIFAR-100).
    Args:
        dataset_name (str): Name of the dataset ("cifar10" or "cifar100").
        source_split (str): "train" or "test"
        root (str): Root directory where the dataset is stored or will be downloaded.
        transform (callable, optional): A function/transform to apply to the data.
        download (bool): Whether to download the dataset if not found locally.
    Returns:
        torch.utils.data.Dataset: The loaded dataset.
    """
    if dataset_name == "cifar10":
        ds = datasets.CIFAR10(
            root=root,
            train=(source_split == "train"),
            transform=transform,
            target_transform=None,
            download=download,
        )
    elif dataset_name == "cifar100":
        ds = datasets.CIFAR100(
            root=root,
            train=(source_split == "train"),
            transform=transform,
            target_transform=None,
            download=download,
        )
    else:
        assert False, f"Unknown CIFAR dataset_name: {dataset_name}"
    return ds


class TransformedSubset(torch.utils.data.Dataset):
    """
    A wrapper for a torch.utils.data.Subset that applies a transform.
    This is useful because Subsets themselves don't have a transform attribute
    that can be set after creation.
    """
    def __init__(self, subset, transform=None):
        self.subset = subset
        self.transform = transform

    def __getitem__(self, index):
        x, y = self.subset[index] # Subset returns data from the original dataset
        if self.transform:
            x = self.transform(x)
        return x, y

    def __len__(self):
        return len(self.subset)

def get_tensor_transform():
    return transforms.Compose([
        transforms.ToTensor(),
    ])

def apply_tensor_transform(data):
    return transforms.functional.to_tensor(data)
    

def get_dataloader(
    dataset,
    transform,
    batch_size,
    shuffle,
    generator,
    num_workers,
):
    dataset_transformed = TransformedSubset(
        dataset, transform=transform
    )
    loader = DataLoader(
        dataset_transformed,
        batch_size=batch_size,
        shuffle=shuffle,
        worker_init_fn=dtu.seed_worker,
        generator=generator,
        num_workers=num_workers,
    )
    return loader
    

def split_data(dataset, ratio, data_split_seed=None):
    split_generator = torch.Generator()
    if data_split_seed is not None:
        split_generator.manual_seed(data_split_seed)

    num_samples = len(dataset)
    num_first = int(ratio * num_samples)
    num_second = num_samples - num_first
    first_subset, second_subset = torch.utils.data.random_split(
        dataset, 
        [num_first, num_second], 
        generator=split_generator
    )
    return first_subset, second_subset
