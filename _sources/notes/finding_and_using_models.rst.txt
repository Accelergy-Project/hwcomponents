Finding and Using Models
========================

This document follows the ``1_finding_and_using_models.ipynb`` tutorial.

``hwcomponents`` supports many different component models. We can list available
component models with the :py:func:`~hwcomponents.find_models.get_models` function. This
function returns a list of :py:class:`~hwcomponents.model.ComponentModel` subclasses.

You may also use the ``hwcomponents --list`` command from the shell.

.. include-notebook:: ../../notebooks/1_finding_and_using_models.ipynb
   :name: listing_available_models
   :language: python

If we know what type of component we would like to model, we can use the
``name_must_include`` argument to :py:func:`~hwcomponents.find_models.get_models` to
find all models that match a given class name.

For example, we can use the ``hwcomponents_cacti`` package to model an SRAM. Once we've
found the model, we can use the ``help`` function to see its documentation and supported
actions.

.. include-notebook:: ../../notebooks/1_finding_and_using_models.ipynb
   :name: finding_components_2
   :language: python

Once we know the model we'd like to use, we can import the model directly and
instantiate components.

.. include-notebook:: ../../notebooks/1_finding_and_using_models.ipynb
   :name: importing_models
   :language: python

If you're unsure of which component model you'd like to use, there are other ways to
invoke a model. There are three ways to find a component model:

1. Import the model from a module and use it directly.
2. Ask hwcomponents to select the best model for a given component. hwcomponents will
   select the best model for a given component name and attributes, and raise an error
   if no model can be instantiated with the given attributes.
3. Ask for specific properties from hwcomponents. This is similar to the second method,
   but you can ask for the area, energy, latency, or leak power of an action of a
   component directly.

.. include-notebook:: ../../notebooks/1_finding_and_using_models.ipynb
   :name: ways_to_find_components
   :language: python
