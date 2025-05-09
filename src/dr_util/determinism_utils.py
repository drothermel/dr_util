import torch
import numpy as np
import random

def seed_worker(worker_id):
    """
    Seeds a DataLoader worker.
    This function is intended to be used as the worker_init_fn in a DataLoader.
    It ensures that each worker process has a unique and deterministic seed based
    on the main process's initial seed.
    """
    worker_seed = torch.initial_seed() % 2**32
    np.random.seed(worker_seed)
    random.seed(worker_seed)

def set_deterministic(seed):
    """
    Sets various seeds for deterministic behavior in PyTorch, NumPy, and Python's random.
    Args:
        seed (int): The seed value.
    Returns:
        torch.Generator: A PyTorch generator object seeded with the given seed.
    """
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    
    # For CUDA, if available and used (optional, can be commented out if not using GPU)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed) # if using multi-GPU
        # These can make operations slower but are necessary for full determinism on GPU
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # This tries to make PyTorch use deterministic algorithms.
    # Note: Some operations may not have deterministic implementations.
    # If you encounter errors, you might need to set this to False or
    # set the environment variable CUBLAS_WORKSPACE_CONFIG=:4096:8 (for CUDA).
    try:
        torch.use_deterministic_algorithms(True)
    except RuntimeError as e:
        print(f"Warning: Could not enforce all deterministic algorithms: {e}")
        print("For full determinism with CUDA, you might need to set environment variable CUBLAS_WORKSPACE_CONFIG=:16:8 or CUBLAS_WORKSPACE_CONFIG=:4096:8")

    generator = torch.Generator().manual_seed(seed)
    return generator

