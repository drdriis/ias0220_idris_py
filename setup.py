from setuptools import find_packages, setup
import os
from glob import glob
package_name = 'ias0220_idris_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.urdf')),
        (os.path.join('share', package_name, 'config'), glob('config/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='drdriis',

    maintainer_email='idrish@taltech.ee',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'test_node = ias0220_idris_py.test_node:main',
            'walker = ias0220_idris_py.random_walker:main',
            'position_calculator = ias0220_idris_py.odometer:main',
        ],
    },

)
