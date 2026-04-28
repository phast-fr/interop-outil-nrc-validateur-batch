import os
from setuptools import setup


def read(fname) -> str:
    return open(os.path.join(os.path.dirname(__file__), fname), encoding="utf-8").read()


setup(
    name="validateur_batch",
    version="1.0.0",
    author="Maël Le Gall",
    author_email="ans-terminologies@esante.gouv.fr",
    description=("Validation des fichiers d'import en batch"),
    license="MIT",
    url="https://github.com/ansforge/interop-outil-nrc-validateur-batch",
    packages=['validateur_batch', 'test'],
    install_requires=[
        "numpy",
        "openpyxl>=3.1.5",
        "pandas",
        "pyarrow>=23.0.1",
        "python-jsonpath",
        "regex>=2026.2.28",
        "requests",
        "responses",
        "fastapi",
        "pydantic",
        "uvicorn",
    ],
    long_description=read('README.md'),
)
