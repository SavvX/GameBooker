from setuptools import setup, find_packages

setup(
    name='gameroom_reservation',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy',
        'Flask-Login',
        'psutil',
        'requests',
    ],
)