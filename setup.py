from setuptools import find_packages, setup

long_description = ""
with open("README.md") as ifp:
    long_description = ifp.read()

setup(
    name="autocorns",
    version="0.0.2",
    packages=find_packages(),
    install_requires=["eth-brownie", "tqdm", "web3"],
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
    author="zomglings",
    author_email="nkashy1@gmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "autocorns=autocorns.cli:main",
        ]
    },
    include_package_data=True,
)
