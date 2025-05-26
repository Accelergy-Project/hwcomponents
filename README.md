## HardwareComponents
This package includes an interface for estimating the energy and area of
components in hardware architectures.

hwcomponents was written for use in
[CiMLoop](https://github.com/mit-emze/cimloop). Components are also compatible
with [Accelergy](https://github.com/accelergy-project/accelergy).

### Installation

```bash
git clone <this-repo>
cd hwcomponents
pip install .
```

### Usage

#### Creating a new Estimator

Estimators are classes that implement the `EnergyAreaEstimator` interface. Each
estimator must give the name of the components that it supports, its percent
accuracy, and the `get_area` and `leak` methods. Additionally, any methods
decorated with `@actionDynamicEnergy` will be treated as an action that can be
queried for energy.

If any arguments are invalid, the estimator should raise a `ValueError`.

```python
from hwcomponents import EnergyAreaEstimator
from typing import List, Union

# REQUIRED: Declare a new Estimator
class TernaryMAC(EnergyAreaEstimator):
    # REQUIRED: Give the name of the components supported by this Estimator.
    # REQUIRED: Give the percent accuracy of the Estimator.
    component_name: Union[str, List[str]] = 'ternary_mac'
    percent_accuracy_0_to_100 = 80

    def __init__(self, accum_datawidth: int, technology: int):
        self.accum_datawidth = accum_datawidth
        self.technology = technology

        # Raising an error says that this estimator can't estimate,
        # and estimators instead should be used instead. Good error
        # messages are essential for users debugging their designs.
        assert 4 <= accum_datawidth <= 8, \
            f'Accumulation datawidth {accum_datawidth} outside supported ' \
            f'range [4-8]!'
        assert 16 <= technology <= 130, \
            f'Technology node {technology} outside supported range [16, 130]!'

    # The actionDynamicEnergy decorator makes this function visible as an action.
    # The function should return an energy in Joules.
    @actionDynamicEnergy
    def mac(self, clock_gated: bool = False) -> float:
        self.logger.info(f'TernaryMAC Estimator is estimating '
                         f'energy for mac_random.')
        if clock_gated:
            return 0.0
        return 0.002e-12 * (self.accum_datawidth + 0.25) * self.technology**1.1

    # REQUIRED: The get_area function returns the area of this component. It is
    # required in all estimators. The function should return an area in m$^2$.
    def get_area(self) -> float:
        self.logger.info(f'TernaryMAC Estimator is estimating area.')
        return 2 * (self.accum_datawidth + 0.3) * self.technology ** 1.3 * 1e-12
    
    # REQUIRED: The leak function returns the leakage energy per cycle.
    def leak(self, global_cycle_seconds: float) -> float:
        """ Returns the leakage energy per global cycle or an Estimation object 
        with the leakage energy and units. """
        return 1e-3 * global_cycle_seconds # 1mW
```

#### Using Estimators to estimate energy and area

Estimators can be used in two ways:
1. Call estimators directly
2. Gather estimators from multiple modules and pass them to `get_energy` and `get_area`

**Option 1: Call estimators directly**

Estimators can be called directly by instantiating them and calling the desired
action.

```python
# Option 1: Call estimators directly
estimator = TernaryMAC(accum_datawidth=8, technology=16)
mac_energy = estimator.mac()
area = estimator.get_area()
leak_energy_per_cycle = estimator.leak(global_cycle_seconds=1e-9)
```

**Option 2: Gather estimators from multiple modules and pass them to get_energy and get_area**

The `get_estimators` function can be used to gather estimators from multiple
modules. These estimators can be passed to `get_energy` and `get_area` to get
the energy and area of a component.

The `get_energy` and `get_area` functions will find the best estimator for the
given query and return an `Estimation` object. The `Estimation` object has a
`value` attribute that contains the estimated energy or area. It also has a
`messages` attribute with a list of any messages from the estimators.

```python
# Option 2: Gather estimators from multiple modules and pass them to get_energy and get_area
from hwcomponents import get_estimators, get_energy, get_area
estimators = get_estimators('library-plug-in/*.py')
mac_energy = get_energy(estimators, 'ternary_mac', {'accum_datawidth': 8, 'technology': 16}, 'mac', {'clock_gated': True}).value
area = get_area(estimators, 'ternary_mac', {'accum_datawidth': 8, 'technology': 16}).value

mac_energy_estimation = get_energy(estimators, 'ternary_mac', {'accum_datawidth': 8, 'technology': 16}, 'mac', {'clock_gated': True})
for message in mac_energy_estimation.messages:
    print(message)
```
