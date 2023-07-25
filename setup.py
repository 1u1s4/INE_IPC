from setuptools import setup, find_packages
setup(
    name='INEipc',
    version='1.3.1',
    author='Luis Alfredo Alvarado Rodríguez',
    description='ETL para el informe mensual de IPC.',
    long_description='',
    url='https://github.com/1u1s4/INEipc.git',
    keywords='development, setup, setuptools',
    python_requires='>=3.7',
    packages=find_packages(),
    py_modules=['DatosIPC', 'DescriptorIPC', 'SqlIPC'],
    install_requires=[
        'fredapi',
        'xlrd==2.0.1',
        'xlsxwriter',
        'pyodbc',
        'requests',
        'bs4',
        'numpy',
        'pandas',
        'pyarrow',
        'utilsjo @ git+https://github.com/1u1s4/utilsjo.git',
        'INEcodex @ git+https://github.com/1u1s4/INEcodex.git',
        'INEfnts @ git+https://github.com/1u1s4/INEfnts.git',
    ],
    package_data={
        'INEipc': ['db_pack/*', 'datos/*'],
    },
    include_package_data=True,
)