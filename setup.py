from setuptools import setup, find_packages

setup(
    name="pkm",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask>=2.0.0',
        'flask-login>=0.5.0',
        'werkzeug>=2.0.0',
        'markdown>=3.3.0'
    ],
)
