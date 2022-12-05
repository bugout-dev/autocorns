from setuptools import find_packages, setup

long_description = ""
with open("README.md") as ifp:
    long_description = ifp.read()

setup(
    name="autocorns",
    version="0.1.0",
    packages=find_packages(),
    package_data={"autocorns": ["build/contracts/*.json", "autocorns/*.sql"]},
    include_package_data=True,
    install_requires=["eth-brownie", "requests", "tqdm", "web3"],
    extras_require={
        "dev": [
            "black",
            "moonworm >= 0.1.14",
        ],
        "distribute": ["setuptools", "twine", "wheel"],
    },
    description="A team of Crypto Unicorn bots",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Moonstream DAO",
    author_email="engineering@moonstream.to",
    url="https://github.com/bugout-dev/autocorns",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "autocorns=autocorns.cli:main",
        ]
    },
)
