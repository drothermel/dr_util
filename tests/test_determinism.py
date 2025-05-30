import numpy as np
import torch
from PIL import Image
from torchvision import transforms

import dr_util.data_utils as du
import dr_util.determinism_utils as dtu


class DummyDataset(torch.utils.data.Dataset):
    def __init__(self, num_samples=20, image_size=(32, 32), num_classes=10):
        self.num_samples = num_samples
        self.image_size = image_size
        self.num_classes = num_classes
        self.data = []
        self.targets = []

        for _ in range(self.num_samples):
            dummy_image_array = np.uint8(
                np.random.randint(0, 256, (*self.image_size, 3))
            )
            pil_image = Image.fromarray(dummy_image_array, "RGB")
            self.data.append(pil_image)
            self.targets.append(np.random.randint(0, self.num_classes))

    def __len__(self):
        return self.num_samples

    def __getitem__(self, index):
        return self.data[index], self.targets[index]


def test_data_split_vs_general_determinism():
    dataset = DummyDataset(num_samples=100)

    # Test changing data_split_seed
    _ = dtu.set_deterministic(15)
    model1 = torch.nn.Linear(3 * 32 * 32, 10)
    train_d1, val_d1 = du.split_data(dataset, 0.1, data_split_seed=1)
    train_d2, val_d2 = du.split_data(dataset, 0.1, data_split_seed=2)

    # Verify that changing general seed doesn't affect data split
    # but does affect model init
    _ = dtu.set_deterministic(20)
    model2 = torch.nn.Linear(3 * 32 * 32, 10)
    train_d3, val_d3 = du.split_data(dataset, 0.1, data_split_seed=1)

    # Verify that changing general seed back works
    _ = dtu.set_deterministic(15)
    model3 = torch.nn.Linear(3 * 32 * 32, 10)

    # Data Split Tests
    i1, l1 = train_d1[3]
    i2, l2 = train_d2[3]
    i3, l3 = train_d3[3]
    sum_d1 = torch.sum(transforms.functional.to_tensor(i1))
    sum_d2 = torch.sum(transforms.functional.to_tensor(i2))
    sum_d3 = torch.sum(transforms.functional.to_tensor(i3))
    assert train_d1.indices == train_d3.indices
    assert val_d1.indices == val_d3.indices
    assert sum_d1 == sum_d3
    assert l1 == l3
    assert train_d1.indices != train_d2.indices
    assert val_d1.indices != val_d2.indices
    assert sum_d1 != sum_d2

    # General Tests
    m1_sum = sum(p.sum().item() for p in model1.parameters())
    m2_sum = sum(p.sum().item() for p in model2.parameters())
    m3_sum = sum(p.sum().item() for p in model3.parameters())
    assert m1_sum == m3_sum
    assert m1_sum != m2_sum
