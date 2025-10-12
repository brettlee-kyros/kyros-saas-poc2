"""Setup file for shared-config package."""
from setuptools import find_packages, setup

setup(
    name="shared-config",
    version="0.1.0",
    description="Shared JWT configuration and validation for Kyros SaaS PoC",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=[
        "PyJWT==2.8.0",
        "pydantic>=2.10.0,<3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.0",
            "pytest-asyncio>=0.24.0",
        ],
    },
)
