"""
Setup configuration for CI/CD Pipeline Generator.

Uses setuptools with declarative configuration from pyproject.toml.
This file is provided for backward compatibility with older tools.
"""

from setuptools import find_packages, setup

setup(
    name="cicd-pipeline-generator",
    version="1.0.0",
    description="Generate CI/CD pipeline configurations for multiple platforms",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Mani",
    author_email="myfamily9006@gmail.com",
    url="https://github.com/example/cicd-pipeline-generator",
    packages=find_packages(include=["src", "src.*"]),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "cicd-gen=src.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Build Tools",
    ],
    keywords="cicd devops pipeline github-actions gitlab-ci jenkins azure-devops circleci",
    license="MIT",
    zip_safe=False,
)
