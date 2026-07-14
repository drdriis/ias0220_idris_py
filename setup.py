import os
from glob import glob

from setuptools import find_packages, setup


package_name = 'ias0220_idris_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        (
            'share/' + package_name,
            ['package.xml'],
        ),
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py'),
        ),
        (
            os.path.join('share', package_name, 'config'),
            glob('config/*.rviz'),
        ),
        (
            os.path.join('share', package_name, 'data', 'images'),
            glob('data/images/*'),
        ),
        (
            os.path.join('share', package_name, 'urdf'),
            glob('urdf/*'),
        ),
        (
            os.path.join('share', package_name, 'config'),
            glob('config/*.rviz') + glob('config/*.yaml'),
        ),
        (
            os.path.join('share', package_name, 'map'),
            glob('map/*'),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='drdriis',
    maintainer_email='idrish@taltech.ee',
    description='Camera calibration assignment for IAS0220',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'simple_control = ias0220_idris_py.simple_control:main',
        ],
    },
)
