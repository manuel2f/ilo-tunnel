from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ilo-tunnel",
    version="1.0.0",
    author="Manuel Fernández",
    description="Una aplicación GUI para crear túneles SSH para HP ProLiant ILO",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tu-usuario/ilo-tunnel",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "PyQt6>=6.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ilo-tunnel=ilo_tunnel.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ilo_tunnel": ["resources/**/*"],
    },
)
