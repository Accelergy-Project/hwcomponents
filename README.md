<div align="center">

<img src="https://capsule-render.vercel.app/api?type=rect&color=0:004CFF,100:00CFFF&height=100&section=header&text=HWComponents&fontSize=52&fontColor=ffffff&fontAlignY=55" alt="HWComponents" />

***Area, energy, latency, and leak power models for hardware components.***

<br>

[![PyPI](https://img.shields.io/pypi/v/hwcomponents?style=for-the-badge&logo=pypi&logoColor=white&labelColor=3775A9&color=0B4F6C)](https://pypi.org/project/hwcomponents/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=1E415E)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-A31F34?style=for-the-badge&labelColor=2D2D2D)](https://opensource.org/licenses/MIT)
[![Docs](https://img.shields.io/badge/Docs-online-0A7BBB?style=for-the-badge&logo=readthedocs&logoColor=white&labelColor=1A1A1A)](https://accelergy-project.github.io/hwcomponents/)

[![CI](https://img.shields.io/github/actions/workflow/status/Accelergy-Project/hwcomponents/publish.yaml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=CI&labelColor=24292F&color=2EA043)](https://github.com/Accelergy-Project/hwcomponents/actions)
[![Code style: black](https://img.shields.io/badge/code_style-black-000000?style=for-the-badge&logo=python&logoColor=white&labelColor=2D2D2D)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-2EA043?style=for-the-badge&logo=github&logoColor=white&labelColor=24292F)](https://github.com/Accelergy-Project/hwcomponents/pulls)

</div>

---

HWComponents provides area, energy, latency, and leak power estimates for hardware components in hardware architectures. It is part of the [CiMLoop](https://github.com/mit-emze/cimloop) project and serves as the estimation backend for [AccelForge](https://github.com/Accelergy-Project/accelforge).

Learn more at the [website](https://accelergy-project.github.io/hwcomponents/) or on [GitHub](https://github.com/Accelergy-Project/hwcomponents).

## ⚡ Features

- **Simple Python API** for writing area, energy, latency, and leak power models. New models can be written in minutes.
- **Automatic parameter scaling** across configurations, including scaling to different technology nodes.
- **Plugin ecosystem** that automatically gathers components from installed Python packages.
- **Included model packages** for multiple projects, plus a general-purpose component library.

## 📦 Install

```bash
# Core package
pip install hwcomponents

# Model packages
pip install hwcomponents-cacti
pip install hwcomponents-neurosim
pip install hwcomponents-adc
pip install hwcomponents-library

# List available models
hwc --list
```

## 🧪 Examples

See the [`notebooks/`](notebooks) directory for tutorials, and the [docs](https://accelergy-project.github.io/hwcomponents/) for the full API.

## 📚 Cite

If you use HWComponents in your work, please cite this repository and the CiMLoop project:

```bibtex
@software{hwcomponents,
  author={Andrulis, Tanner},
  title={HWComponents},
  url={https://github.com/Accelergy-Project/hwcomponents},
  license={MIT},
}

@INPROCEEDINGS{cimloop,
  author={Andrulis, Tanner and Emer, Joel S. and Sze, Vivienne},
  booktitle={2024 IEEE International Symposium on Performance Analysis of Systems and Software (ISPASS)},
  title={CiMLoop: A Flexible, Accurate, and Fast Compute-In-Memory Modeling Tool},
  year={2024},
  pages={10-23},
  doi={10.1109/ISPASS61541.2024.00012}
}
```
