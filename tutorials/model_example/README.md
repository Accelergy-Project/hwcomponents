### Model Example

This directory contains an example hwcomponents model.

To create a new model, copy this directory to a new name and edit to your needs.

Please keep the following in mind while you're changing the model:
- The model name should be prefixed with `hwcomponents_`. This allows HWComponents
  to find the model when it is installed.
- The `__init__.py` file should import all Model classes that you'd like to be
  visible to HWComponents.
- If you're iterating on an model, you can use the `pip3 install -e .` command to
  install the model in editable mode. This allows you to make changes to the
  model without having to reinstall it.

To install the model, run the following command:
```bash
# Install the model
pip3 install .

# Check that the model is installed
hwc --list | grep TernaryMAC
```