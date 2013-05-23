from setuptools import setup, find_packages

version = '0.1'

setup(name='makerbot_tools',
      version=version,
      description="",
      long_description="""\
""",
      classifiers=[],
      keywords='',
      author='CKAB',
      author_email='',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'python-daemon',
          'mock',
          'lockfile',
          'argparse',
          'pyserial',
          'conveyor',
          'waitress',
          'bottle',
      ],
      entry_points="""
      [console_scripts]
      conveyor-server=makerbot_tools.scripts:conveyor_server
      conveyor-client=makerbot_tools.scripts:conveyor_client
      conveyor-ui=makerbot_tools.scripts:serve
      print=makerbot_tools.scripts:conveyor_print
      s3b_print=makerbot_tools.s3b_printer:main
      """,
      )
