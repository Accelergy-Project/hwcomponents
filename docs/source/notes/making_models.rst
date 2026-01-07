Making Models
=============

This document follows the ``2_making_models.ipynb`` tutorial.

Basic Components
----------------

Models can be created by subclassing the :py:class:`~hwcomponents.model.ComponentModel`
class. Models estimate the energy, area, and leakage power of a component. Each model
requires the following:

- ``component_name``: The name of the component. This may also be a list of components if
  multiple aliases are used.
- ``priority``: This is used to break ties if multiple models support a given query.
- A call to ``super().__init__(area, leak_power, subcomponents)``. This is used to
  initialize the model and set the area and leakage power.

Models can also have actions. Actions are functions that return a tuple of ``(energy,
latency)`` for a specific action. For the TernaryMAC model, we have an action called
``mac`` that returns the energy and latency of a ternary MAC operation. The
:py:func:`~hwcomponents.model.action` decorator makes this function visible as an
action. The function should return ``(energy_in_Joules, latency_in_seconds)``.

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
- ``latency_scaling_function``: The scaling function to use for latency. Use ``None`` if
  no scaling should be done.
- ``leak_scaling_function``: The scaling function to use for leakage power. Use ``None``
  if no scaling should be done.

**Note: Area, Energy, Latency, and Leak Power are always in alphabetical order in the
function arguments.**

Many different scaling functions are defined and available in
:py:mod:`hwcomponents.scaling`.

.. include-notebook:: ../../notebooks/2_making_models.ipynb
   :name: example_mac
   :language: python

Scaling by Number of Bits
-------------------------

Some actions may depend on the number of bits being accessesed. For example, you may
want to charge for the energy and latency per bit of a DRAM read. To do this, you can
use the ``bits_per_action`` argument of the :py:func:`~hwcomponents.model.action`
decorator. This decorator takes a string that is the name of the parameter to scale by.
For example, we can scale the energy and latency of a DRAM read by the number of bits
being read. In this example, the DRAM yields ``width`` bits per read, so energy and
latency are scaled by ``bits_per_action / width``.

.. include-notebook:: ../../notebooks/2_making_models.ipynb
   :name: scaling_by_number_of_bits
   :language: python

Compound Models
---------------

We can create compound models by combining multiple component models. Here, we'll show
the ``SmartBufferSRAM`` model from the ``hwcomponents-library`` package.This is an SRAM
with an address generator that sequentially reads addresses in the SRAM.

We'll use the following components:

- A SRAM buffer
- Two registers: one that that holds the current address, and one that holds the
  increment value
- An adder that adds the increment value to the current address

One new functionality is used here. The ``subcomponents`` argument to the
:py:class:`~hwcomponents.model.ComponentModel` constructor is used to register
subcomponents.

The area, energy, latency, and leak power of subcomponents will NOT be scaled by the
component's ``area_scale``, ``energy_scale``, ``latency_scale``, and ``leak_scale``; if
you want to scale the subcomponents, multiply the subcomponents' ``area_scale``,
``energy_scale``, ``latency_scale``, and ``leak_scale`` by the desired scale factor.

.. include-notebook:: ../../notebooks/2_making_models.ipynb
   :name: smartbuffer_sram
   :language: python

The latency of subcomponents is generally summed. However, if the subcomponents are
pipelined for a given action, then the ``pipelined_subcomponents`` argument to the
:py:func:`~hwcomponents.model.action` decorator should be set to True. This will cause
the latency of the action to be the max of the latency returned and all subcomponent
latencies.

Installing Models and Making them Globally Visible
--------------------------------------------------

An example model is provided in the ``notebooks/model_example`` directory, which can be
installed with the following command:

.. code-block:: bash

    cd notebooks/model_example
    pip3 install .

The ``README.md`` file in the ``notebooks/model_example`` directory contains information
on how to make models installable. Keep the following in mind while you're changing the
model:

- The model name should be prefixed with ``hwcomponents_``. This allows HWComponents
  to find the model when it is installed.
- The ``__init__.py`` file should import all Model classes that you'd like to be
  visible to HWComponents.
- If you're iterating on an model, you can use the ``pip3 install -e .`` command to
  install the model in editable mode. This allows you to make changes to the
  model without having to reinstall it.
