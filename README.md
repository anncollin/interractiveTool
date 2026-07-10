# Interactive Visualization Tool

Interactive t-SNE visualization tool for exploring well embeddings and their nearest neighbors.

The application supports two dimensionality-reduction backends:

* **scikit-learn**, CPU-based and compatible with Ubuntu and macOS
* **cuML**, GPU-accelerated and available on Linux computers with a compatible NVIDIA GPU

When configured with automatic backend selection, the application uses cuML when available and falls back to scikit-learn otherwise.

## 1. Create the Conda environment

### Clone the repository

```bash
git clone <repository-url>
cd interractiveTool
```

Replace `<repository-url>` with the URL of this GitHub repository.

### Create the environment

The repository contains an `environment.yml` file defining the required libraries.

```bash
conda env create -f environment.yml
```

This creates an environment named `visu`.

### Activate the environment

```bash
conda activate visu
```

### Run the application

From the repository directory:

```bash
python main.py
```

The application should report:

```text
Using scikit-learn CPU backend
```

### Update an existing environment

After changes to `environment.yml`, update the environment with:

```bash
conda env update -n visu -f environment.yml --prune
```

The `--prune` option removes dependencies that are no longer listed in the YAML file.

## 2. Optional GPU acceleration with cuML

cuML is optional. The visualization tool works without it by using scikit-learn.

cuML requires:

* Linux
* A compatible NVIDIA GPU
* A working NVIDIA driver
* A CUDA version supported by the installed RAPIDS release

cuML cannot be installed natively on macOS.

### Check NVIDIA GPU availability

```bash
nvidia-smi
```

If this command does not detect an NVIDIA GPU, continue using the scikit-learn backend.

### Activate the environment

```bash
conda activate visu
```

### Install cuML

Choose a CUDA version compatible with the NVIDIA driver installed on the computer. For example:

```bash
conda install -c rapidsai -c conda-forge -c nvidia cuml cuda-version=12.8
```

The appropriate CUDA version can be selected using the official RAPIDS installation selector:

https://docs.rapids.ai/install/

The NVIDIA driver must support the requested CUDA version. The CUDA compatibility information displayed by `nvidia-smi` can help select an appropriate version.

### Verify the installation

```bash
python -c "import cuml; print('cuML version:',cuml.__version__)"
```

Then run the application:

```bash
python main.py
```

When cuML is detected, the application should report:

```text
Using cuML GPU backend
```

Otherwise, it will use:

```text
Using scikit-learn CPU backend
```

## 3. Create a `visu` launcher command

A shell launcher makes it possible to start the application from any directory by typing:

```bash
visu
```

The command will:

1. Activate the `visu` Conda environment
2. Move to the `interractiveTool` directory
3. Run `main.py`

Use `&&` between the commands. This ensures that the next command runs only when the previous command succeeds.

### Ubuntu with Bash

Open the Bash configuration file:

```bash
nano ~/.bashrc
```

Add the following function at the end of the file:

```bash
visu() {
    conda activate visu &&
    cd ~/Desktop/Nucleoles/interractiveTool &&
    python main.py
}
```

Save the file with `Ctrl+O`, press Enter, and exit with `Ctrl+X`.

Reload the Bash configuration:

```bash
source ~/.bashrc
```

The application can now be started from any directory with:

```bash
visu
```

### macOS with Zsh

The default shell on recent macOS versions is Zsh.

Open the Zsh configuration file:

```bash
nano ~/.zshrc
```

Add:

```bash
visu() {
    conda activate visu &&
    cd ~/Desktop/Nucleoles/interractiveTool &&
    python main.py
}
```

Change the directory in the function if the repository is stored elsewhere.

Reload the configuration:

```bash
source ~/.zshrc
```

Start the application with:

```bash
visu
```

### Alternative single-line alias

A single-line alias can also be used:

```bash
alias visu='conda activate visu && cd ~/Desktop/Nucleoles/interractiveTool && python main.py'
```

Add this line to `~/.bashrc` on Ubuntu or `~/.zshrc` on macOS, then reload the corresponding configuration file.

The shell function is recommended because it is easier to read and modify.

## Conda initialization

If the launcher reports that `conda activate` is unavailable, initialize Conda for the current shell.

For Bash:

```bash
conda init bash
source ~/.bashrc
```

For Zsh:

```bash
conda init zsh
source ~/.zshrc
```

Then try again:

```bash
visu
```

## Remove the environment

To completely remove the environment:

```bash
conda deactivate
conda env remove -n visu
```

## Backend configuration

The backend can be selected in `config.py`.

For automatic selection:

```python
TSNE_BACKEND="auto"
```

With this setting:

* cuML is used when it is installed
* scikit-learn is used when cuML is unavailable

This allows the same source code to run on Linux GPU computers, Linux CPU computers, and macOS.
