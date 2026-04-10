from setuptools import setup, find_packages

setup(
    name="cme",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["click"],
    entry_points={
        "console_scripts": [
            "cme = cloudmesh.ai.main:cli",
        ],
    },
)
