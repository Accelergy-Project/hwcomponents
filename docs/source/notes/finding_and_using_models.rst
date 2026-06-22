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

How the Best Model is Chosen
----------------------------

When several models support a query, hwcomponents tries them in order and uses the
first one that returns successfully. If a model raises an error, the next one is tried.
The order is determined by the following, in this order:

1. ``priority``, higher first. Defaults to 0.5.
2. The number of provided action arguments that the action accepts, more first (only
   when an action is queried).
3. The number of provided attributes that the init function accepts, more first.
4. The number of the action's defaulted arguments not provided by the query, fewer
   first (only when an action is queried).
5. The number of the init function's defaulted arguments not provided by the query,
   fewer first.
6. The fully-qualified class name (module and qualified name), lower-alphabetically
   first.

In short, the highest-priority model wins, and ties are broken in favor of the model
that most closely matches the query. See
:py:func:`~hwcomponents.select_models.get_model` for the API.
