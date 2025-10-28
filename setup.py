from setuptools import setup, find_packages

setup(
    name="aks",
    version="1.0.0",
    description="Ask LLM Tool CLI",
    author="Nathan Slager <slagernate@gmail.com>",
    packages=find_packages(),
    install_requires=["openai>=1.0"],
    entry_points={
        "console_scripts": ["aks = aks.main:main"]
    },
)
