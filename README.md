# dr_util

A comprehensive Python utility library for ML research, providing robust tools for metrics collection, data management, configuration validation, and reproducible experiments.

## 🚀 Features

- **🏗️ Type-Safe Architecture**: Complete type coverage with mypy strict mode
- **📊 Advanced Metrics System**: Hierarchical metrics collection with multiple logger backends
- **🔄 Reproducibility Tools**: Deterministic seeding for PyTorch, NumPy, and CUDA
- **📁 Universal File I/O**: Multi-format file handling (JSON, JSONL, PKL, NPY, YAML)
- **⚙️ Config Validation**: Schema-based configuration validation for Hydra configs  
- **🗄️ Data Loading**: PyTorch utilities with transforms and deterministic splitting
- **☁️ Cloud Integration**: S3 utilities and Roam Research API wrapper
- **🧪 Research Scripts**: Paper extraction, SLURM monitoring, and S3 management tools

## 📦 Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone <repo-url>
cd dr_util

# Create virtual environment (Python 3.12+)
uv venv

# Install with development dependencies
uv sync --group dev --group test
```

### Using pip

```bash
pip install -e .
# For development
pip install -e ".[dev,test]"
```

## 🛠️ Development Setup

### Quality Assurance

This project uses a comprehensive QA setup with zero tolerance for type and lint errors:

```bash
# Run all checks (ruff + mypy)
ckdr

# Individual commands
uv run ruff check       # Linting  
uv run ruff format      # Formatting
uv run mypy src/        # Type checking
uv run pytest          # Testing
```

### Pre-commit Configuration

The project includes extensive ruff configuration with 50+ rules for code quality, including:
- Type annotations (`ANN`)
- Security checks (`S`) 
- Performance optimizations (`PERF`)
- ML-specific numpy rules (`NPY`)

## 📚 Core Modules

### 📊 Metrics System (`dr_util.metrics`)

Comprehensive metrics collection with multiple backends and aggregation strategies:

```python
from dr_util.metrics import Metrics, LoggerType

# Initialize with Hydra config
metrics = Metrics(cfg)

# Log training metrics
metrics.train({"loss": 0.5, "accuracy": 0.85}, ns=32)  # batch_size=32
metrics.val({"loss": 0.3, "accuracy": 0.92}, ns=16)

# Aggregate and log results
metrics.agg_log("train")  # Logs aggregated training metrics
metrics.agg_log("val")    # Logs aggregated validation metrics
```

**Features:**
- **Multiple Loggers**: Hydra integration and JSONL file output
- **Smart Aggregation**: Batch-weighted averaging for accurate metrics
- **Type Dispatch**: Automatic handling of different data types
- **Hierarchical Structure**: Train/validation metric separation

### 🔄 Determinism (`dr_util.determinism_utils`)

Ensure reproducible ML experiments across different environments:

```python
from dr_util.determinism_utils import set_deterministic, seed_worker
from torch.utils.data import DataLoader

# Set global deterministic behavior
generator = set_deterministic(42)

# Use with DataLoader for reproducible data loading
dataloader = DataLoader(
    dataset, 
    batch_size=32,
    worker_init_fn=seed_worker,  # Seeds each worker
    generator=generator
)
```

**Handles:**
- PyTorch (CPU + CUDA)
- NumPy random state
- Python random module
- CUDA deterministic algorithms
- DataLoader worker seeding

### 📁 File I/O (`dr_util.file_utils`)

Universal file operations with automatic format detection:

```python
from dr_util.file_utils import load_file, dump_file, load_files

# Automatic format detection
data = load_file("config.yaml")        # YAML
results = load_file("results.json")    # JSON  
embeddings = load_file("vectors.npy")  # NumPy

# Batch operations
configs = load_files(["train.yaml", "eval.yaml", "model.yaml"])

# Memory mapping for large arrays
large_array = load_file("huge_matrix.npy", mmm="r")
```

**Supported Formats:**
- JSON, JSONL (streaming support)
- YAML (via OmegaConf)
- NumPy arrays (with memory mapping)
- Pickle files
- Plain text

### 🗄️ Data Loading (`dr_util.data_utils`)

PyTorch utilities with emphasis on reproducibility:

```python
from dr_util.data_utils import get_cifar_dataset, split_data, get_dataloader

# Load CIFAR with transforms
dataset = get_cifar_dataset("cifar10", "train", "./data", transform=transform)

# Deterministic train/val split
train_set, val_set = split_data(dataset, ratio=0.8, data_split_seed=42)

# Create reproducible dataloaders
train_loader = get_dataloader(
    train_set, transform=train_transform, batch_size=32, 
    shuffle=True, generator=generator, num_workers=4
)
```

### ⚙️ Config Validation (`dr_util.config_verification`)

Schema-based validation for Hydra configurations:

```python
from dr_util.config_verification import validate_cfg
from dr_util.schemas import get_schema

# Validate against schema
schema_cls = get_schema("uses_metrics")
is_valid = validate_cfg(cfg, "uses_metrics", get_schema)

# Pretty-print configs for debugging
from dr_util.config_verification import get_cfg_str
print(get_cfg_str(cfg))
```

### ☁️ Cloud Integration

#### S3 Management (`dr_util.api_wrappers.aws_utils`)

Smart S3 operations with timestamp checking:

```python
from dr_util.api_wrappers.aws_utils import download_file_if_needed

# Only downloads if S3 version is newer
success = download_file_if_needed(
    bucket="my-bucket",
    key="models/latest.pt", 
    local_path="./models/latest.pt"
)
```

#### Roam Research API (`dr_util.api_wrappers.roam_utils`)

Complete Roam Research backend integration:

```python
from dr_util.api_wrappers.roam_utils import initialize_graph, create_block

# Initialize client
client = initialize_graph({"token": "your-token", "graph": "your-graph"})

# Create content
create_block(client, {
    "location": {"parent-uid": "page-uid", "order": 0},
    "block": {"string": "Your content here"}
})
```

## 🧪 Research Scripts

### S3 File Manager

Download research datasets and models:

```bash
# Configure in conf/s3man.yaml
uv run s3man

# Or with overrides
uv run s3man source.key_name=models/bert.pt output.file=models/bert.pt
```

### Paper Extraction Tools

```bash
# Available in scripts/paper_extract/
- bibtex_extractor.py    # Extract BibTeX from papers
- read_cvf_papers.py     # CVF paper metadata
- read_openreview_api.py # OpenReview submissions  
- read_pmlr_rss.py      # PMLR proceedings
```

### SLURM Monitoring

```bash
# Available in scripts/slurm_inspect/
- idle_gpus.py    # Find available GPUs
- slurm_info.py   # Cluster status monitoring
```

## 📊 Configuration

### Hydra Integration

The library is designed for Hydra-based configuration management:

```yaml
# configs/base_config.yaml
defaults:
  - paths: mac
  - data: cifar10

metrics:
  loggers: ["hydra", "json"]
  init:
    batch_size: "list"
    loss: "batch_weighted_avg_list"
    accuracy: "batch_weighted_avg_list"

determinism:
  seed: 42
  use_deterministic_algorithms: true
```

### Development Configuration

Comprehensive tooling configuration in `pyproject.toml`:

- **Ruff**: 50+ lint rules optimized for ML code
- **MyPy**: Strict type checking with ML-specific settings  
- **Pytest**: Parallel execution with coverage reporting
- **Coverage**: ML-aware exclusions for GPU/debug code

## 🧩 Examples

### Complete Training Setup

```python
from dr_util.metrics import Metrics
from dr_util.determinism_utils import set_deterministic
from dr_util.data_utils import get_cifar_dataset, split_data

# Reproducible setup
generator = set_deterministic(42)

# Data loading
dataset = get_cifar_dataset("cifar10", "train", "./data")
train_set, val_set = split_data(dataset, 0.8, data_split_seed=42)

# Metrics tracking  
metrics = Metrics(cfg)

# Training loop
for epoch in range(num_epochs):
    for batch_idx, (data, target) in enumerate(train_loader):
        # ... training code ...
        
        # Log metrics
        metrics.train({
            "loss": loss.item(),
            "accuracy": accuracy
        }, ns=data.size(0))
    
    # Aggregate and log epoch metrics
    metrics.agg_log("train")
```

## 🤝 Contributing

1. **Type Safety**: All code must pass `mypy --strict`
2. **Code Quality**: Zero ruff violations allowed  
3. **Testing**: Add tests for new functionality
4. **Documentation**: Update docstrings and README

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=html

# Specific test categories  
uv run pytest -m "not slow"      # Skip slow tests
uv run pytest -m integration     # Only integration tests
```

## 📄 License

[Add your license information here]

## 🔗 Dependencies

### Core Dependencies
- **PyTorch**: Deep learning framework
- **Hydra**: Configuration management  
- **OmegaConf**: Configuration handling
- **NumPy**: Numerical computing
- **Boto3**: AWS S3 integration

### Development Dependencies  
- **Ruff**: Fast linting and formatting
- **MyPy**: Static type checking
- **Pytest**: Testing framework with plugins
- **Types-requests**: Type stubs for requests

## 📈 Project Status

- ✅ **Type Coverage**: 100% with mypy strict mode
- ✅ **Code Quality**: Zero lint violations
- ✅ **Testing**: Comprehensive test suite
- ✅ **Documentation**: Fully documented APIs
- 🔄 **Active Development**: Regular updates and improvements

---

**Built for ML Researchers** • **Type-Safe** • **Production-Ready**