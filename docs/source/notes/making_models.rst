Making Models
=============

This document follows the ``2_making_models.ipynb`` tutorial.

Basic Components
----------------

Models can be created by subclassing the :py:class:`hwcomponents.EnergyAreaModel` class.
Models estimate the energy, area, and leakage power of a component. Each model requires
the following:

- ``component_name``: The name of the component. This may also be a list of components if
  multiple aliases are used.
- ``priority_0_to_100``: The percent accuracy of the model. This is used to
  break ties if multiple models support a given query.
- A call to ``super().__init__(area, leak_power, subcomponents)``. This is used to
  initialize the model and set the area and leakage power.

Models can also have actions. Actions are functions that return an energy of a specific
action. For the TernaryMAC model, we have an action called ``mac`` that returns the
energy of a ternary MAC operation. The :py:func:`hwcomponents.actionDynamicEnergy`
decorator makes this function visible as an action. The function should return an energy
in Joules.

Models can also be scaled to support a range of different parameters. For example,
the TernaryMAC model can be scaled to support a range of different technology nodes.
This is done by calling the ``self.scale`` function in the ``__init__`` method of the
model. The ``self.scale`` function takes the following arguments:
- ``parameter_name``: The name of the parameter to scale.
- ``parameter_value``: The value of the parameter to scale.
- ``reference_value``: The reference value of the parameter.
- ``area_scaling_function``: The scaling function to use for area. Use ``None`` if no
  scaling should be done.
- ``energy_scaling_function``: The scaling function to use for dynamic energy. Use
  ``None`` if no scaling should be done.
- ``leak_scaling_function``: The scaling function to use for leakage power. Use ``None``
  if no scaling should be done.

Many different scaling functions are defined and available in
:py:mod:`hwcomponents.scaling`.

.. include-notebook:: ../../tutorials/2_making_models.ipynb
   :name: example_mac
   :language: python

Scaling by Number of Bits
-------------------------

Some actions may depend on the number of bits being accessesed. For example, you may
want to charge for the energy per bit of a DRAM read. To do this, you can use the
``bits_per_action`` argument of the :py:func:`hwcomponents.actionDynamicEnergy`
decorator. This decorator takes a string that is the name of the parameter to scale by.
For example, we can scale the energy of a DRAM read by the number of bits being read. In
this example, the DRAM yields ``width`` bits per read, so energy is scaled by
``bits_per_action / width``.

.. include-notebook:: ../../tutorials/2_making_models.ipynb
   :name: scaling_by_number_of_bits
   :language: python

Compound Models
------------------

We can create compound models by combining multiple component models. Here, we'll show
the ``SmartbufferSRAM`` model from the ``hwcomponents-library`` package.This is an SRAM
with an address generator that sequentially reads addresses in the SRAM.

We'll use the following components:

- A SRAM buffer
- Two registers: one that that holds the current address, and one that holds the
  increment value.
- An adder that adds the increment value to the current address.

One new functionality is used here. The ``subcomponents`` argument to the
:py:class:`hwcomponents.EnergyAreaModel` constructor is used to register subcomponents.

The area, energy, and leak power of subcomponents will NOT be scaled by the component's
``energy_scale``, ``area_scale``, or ``leak_scale``; if you want to scale the
subcomponents, multiply their ``energy_scale``, ``area_scale``, or ``leak_scale`` by the
desired scale factor.

.. include-notebook:: ../../tutorials/2_making_models.ipynb
   :name: smartbuffer_sram
   :language: python
