from setuptools import find_packages, setup

setup(
    name="my_dagster_project",
    packages=find_packages(exclude=["my_dagster_project_tests"]),
    install_requires=[
        "dagster",
        "PyGithub",
        "matplotlib",
        "pandas",
        "nbconvert",
        "nbformat",
        "ipykernel",
        "jupytext",
        "google-api-python-client",
		"google-auth-httplib2",
		"google-auth-oauthlib"
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
