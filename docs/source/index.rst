CiMLoop HWComponents
====================

The HWComponents (Hardware Components) package, part of the `CiMLoop
<https://github.com/mit-emze/cimloop>`_ project, provides an interface for the
estimation of area, energy, latency, and leak power of hardware components in
hardware architectures. Key features in HWComponents include:

- A simple Python API for writing area, energy, latency, and leak power models. New
  models can be written in minutes.
- Automatic scaling of parameters to different configurations, including scaling to
  different technology nodes.
- Pythonic interfaces for finding components, picking the best components for a given
  request, and more.
- Automatic gathering of components from available Python packages. This includes
  support for different models in virtual environments.


Installation
------------
Clone the repository and install with pip. This repository also contains provided
models as submodules.

.. code-block:: bash

   # Install the main package
   pip install hwcomponents

   # Install model packages
   pip install hwcomponents-cacti
   pip install hwcomponents-neurosim
   pip install hwcomponents-adc
   pip install hwcomponents-library

    # List available models
    hwc --list # or hwcomponents --list

hwcomponents API
----------------

.. toctree::
   :maxdepth: 2

   modules
`Code <https://github.com/Accelergy-Project/hwcomponents>`_

Tutorials
---------

See the `tutorials` directory for examples of how to use the package and to create
models. Additional documentation and tutorials are available on this site:

.. toctree::
   :maxdepth: 2

   notes/finding_and_using_models
   notes/making_models

Example Usage
-------------

The following example shows a ternary MAC component written in HWComponents. It uses
scaling to scale the width and technology node of the MAC.

Full examples of how to use the package are available in the ``notebooks`` directory.

.. include-notebook:: ../../notebooks/2_making_models.ipynb
   :name: example_mac
   :language: python

Contributing
------------

Contributions are welcome! Please issue a pull request on GitHub with any changes.

Citing HWComponents
-------------------

If you use this package in your work, please cite the CiMLoop project:

.. code-block:: bibtex

    @INPROCEEDINGS{cimloop,
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
