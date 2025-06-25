from setuptools import setup


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="hwcomponents",
    version="0.5",
    description="Hardware Component Energy+Area Estimators",
    classifiers=[],
    keywords="",
    author="Tanner Andrulis",
    author_email="andrulis@mit.edu",
    license="MIT",
    packages=["hwcomponents", "hwcomponents.scaling"],
    install_requires=[],
    python_requires=">=3.12",
    data_files=[],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "hwcomponents=hwcomponents.hwcomponents:main",
            "hwc=hwcomponents.hwcomponents:main",
        ],
    },
    zip_safe=True,
)
