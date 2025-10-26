"""
FLYO package setup configuration
Install with: pip install -e .
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="flyo",
    version="1.0.0",
    author="Team FLYO - Vivian, Shivashish, Nandana, Monisha",
    author_email="team@flyo.dev",
    description="Natural Language Browser Automation using AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-team/flyo-hackathon",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
    ],
    python_requires=">=3.9",
    install_requires=[
        "openai>=1.3.5",
        "playwright>=1.40.0",
        "colorama>=0.4.6",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "pylint>=3.0.3",
            "mypy>=1.7.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "flyo=flyo.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
