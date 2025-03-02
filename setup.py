# setup.py
from setuptools import setup, find_packages

setup(
    name="ilo-tunnel",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ilo-tunnel=ilo_tunnel.main:main",
        ],
    },
    author="Manuel Fernández",
    author_email="manuel2f@gmail.com",
    description="Una aplicación para gestionar túneles SSH para acceder a interfaces ILO de servidores HP ProLiant",
    keywords="ssh, tunnel, ilo, hp, proliant",
    url="https://github.com/manuel2f/ilo-tunnel",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)