# HWComponents
The HWComponents (Hardware Components) package provides an interface for the estimation
of energy, area, and leakage power of hardware components in hardware architectures. It
is part of the [CiMLoop](https://github.com/mit-emze/cimloop) project. Key features in
HWComponents include:

- A simple Python API for writing energy, area, and leakage power models. New
  models can be written in minutes.
- Automatic scaling of parameters to different configurations, including scaling to
  different technology nodes.
- Pythonic interfaces for finding components, picking the best components for a given
  request, and more.
- Automatic gathering of components from available Python packages. This includes
  support for different models in virtual environments.

Components are also compatible with
[Accelergy](https://github.com/accelergy-project/accelergy).

## Example Usage

The following example shows an adder component written in HWComponents. It uses scaling
to scale the width and technology node of the adder.

Full examples of how to use the package are available in the `tutorials` directory.

```python
from hwcomponents import EnergyAreaModel, actionDynamicEnergy
from hwcomponents.scaling import nlog2n, tech_node_area, tech_node_energy, tech_node_leak

class Adder(EnergyAreaModel):
    component_name = "adder"
    percent_accuracy_0_to_100 = 80

    def __init__(self, width: int, tech_node: float):
        super().__init__(area=10e-12, leak_power=width * 1e-6)

        # Width scales with nlog2n
        self.width = self.scale(
            "width", # Name of the parameter to scale
            width,   # Value of the parameter to scale
            1,       # Value of the parameter to scale from
            nlog2n,  # Scaling function for area
            nlog2n,  # Scaling function for energy
            nlog2n   # Scaling function for leakage
        )

        # Scaling functions for different technology nodes
        self.tech_node = self.scale(
            "tech_node",      # Name of the parameter to scale
            tech_node,        # Value of the parameter to scale
            40e-9,            # Value of the parameter to scale from
            tech_node_area,   # Scaling function for area
            tech_node_energy, # Scaling function for energy
            tech_node_leak,   # Scaling function for leakage
        )

    @actionDynamicEnergy
    def add(self) -> float:
        return 1e-12 # Automatically scaled using self.scale()
```

## Installation
Clone the repository and install with pip. This repository also contains provided
models as submodules.

```bash
# Install the main package
git clone --recurse-submodules <this-repo>
pip install ./hwcomponents

# Install model packages
cd hwcomponents/models
pip3 install ./hwcomponents/models/*

# List available models
hwc --list # or hwcomponents --list
```

## Tutorials

See the `tutorials` directory for examples of how to use the package and to create
models.

## Contributing

Contributions are welcome! Please issue a pull request on GitHub with any changes.

## Citing HWComponents

If you use this package in your work, please cite the CiMLoop project:

```bibtex
@INPROCEEDINGS{10590023,
  author={Andrulis, Tanner and Emer, Joel S. and Sze, Vivienne},
  booktitle={2024 IEEE International Symposium on Performance Analysis of Systems and Software (ISPASS)}, 
  title={CiMLoop: A Flexible, Accurate, and Fast Compute-In-Memory Modeling Tool}, 
  year={2024},
  volume={},
  number={},
  pages={10-23},
  keywords={Performance evaluation;Accuracy;Computational modeling;Computer architecture;Artificial neural networks;In-memory computing;Data models;Compute-In-Memory;Processing-In-Memory;Analog;Deep Neural Networks;Systems;Hardware;Modeling;Open-Source},
  doi={10.1109/ISPASS61541.2024.00012}
}
@INPROCEEDINGS{8942149,
  author={Wu, Yannan Nellie and Emer, Joel S. and Sze, Vivienne},
  booktitle={2019 IEEE/ACM International Conference on Computer-Aided Design (ICCAD)}, 
  title={Accelergy: An Architecture-Level Energy Estimation Methodology for Accelerator Designs}, 
  year={2019},
  volume={},
  number={},
  pages={1-8},
  keywords={Program processors;Electric breakdown;Neural networks;Estimation;Hardware;Energy efficiency;Compounds},
  doi={10.1109/ICCAD45719.2019.8942149}
}
```
