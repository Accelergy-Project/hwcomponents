from setuptools import setup, find_packages


def readme():
    with open("README.md") as f:
        return f.read()


# IMPORTANT: Check the README.md file in this directory for important information on how
# to install models.
# IMPORTANT: Check the README.md file in this directory for important information on how
# to install models.
# IMPORTANT: Check the README.md file in this directory for important information on how
# to install models.
# IMPORTANT: Check the README.md file in this directory for important information on how
# to install models.

setup(
    name="hwcomponents_example",
    version="0.1",
    description="A template hwcomponents model.",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: " "Electronic Design Automation (EDA)",
    ],
    keywords="hardware components energy estimation",
    author="Tanner Andrulis",
    author_email="andrulis@Mit.edu",
    license="MIT",
    install_requires=[],
    python_requires=">=3.12",
    packages=find_packages(include=["hwcomponents_example"]),
    include_package_data=True,
)

# IMPORTANT: Check the README.md file in this directory for important information on how
# to install models.
# IMPORTANT: Check the README.md file in this directory for important information on how
# to install models.
# IMPORTANT: Check the README.md file in this directory for important information on how
# to install models.
# IMPORTANT: Check the README.md file in this directory for important information on how
# to install models.
