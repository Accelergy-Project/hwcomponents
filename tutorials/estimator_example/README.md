### Estimator Example

This directory contains an example hwcomponents estimator.

To create a new estimator, copy this directory to a new name and edit to your needs.

Please keep the following in mind while you're changing the estimator:
- The estimator name should be prefixed with `hwcomponents_`. This allows HWComponents
  to find the estimator when it is installed.
- The `__init__.py` file should import all Estimator classes that you'd like to be
  visible to HWComponents.
- If you're iterating on an estimator, you can use the `pip3 install -e .` command to
  install the estimator in editable mode. This allows you to make changes to the
  estimator without having to reinstall it.

To install the estimator, run the following command:
```bash
# Install the estimator
pip3 install .

# Check that the estimator is installed
hwc --list | grep ternary_mac
```