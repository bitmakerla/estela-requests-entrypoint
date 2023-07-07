from setuptools import find_packages, setup

setup(
    name="estela_requests_entrypoint",
    version="0.0.1-a1",
    description="Requests entrypoint for Estela job runner",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "requests",
        "estela-queue-adapter @ git+https://github.com/bitmakerla/estela-queue-adapter.git",
        "estela-requests @ git+https://github.com/bitmakerla/estela-requests.git@add-scrapeghost",
    ],
    entry_points={
        "console_scripts": [
            "estela-crawl = requests_entrypoint.__main__:main",
            "estela-describe-project = requests_entrypoint.__main__:describe_project",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
)
