from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='ugcal',
      version='0.1',
      description=('Script to syncronize events from meetup.com to Google',
                   'Calendar'),
      long_description=readme(),
      url='http://github.com/UsergroupsLT/ugcal',
      author='Povilas Balzaravicius',
      author_email='pavvka@gmail.com',
      license='MIT',
      packages=['ugcal'],
      include_package_data=True,
      entry_points={
          'console_scripts': ['ugcal-cli=ugcal.ugcal:main']
      },
      install_requires=[
          'google-api-python-client',
          'html2text',
          'httplib2',
          'python-dateutil',
          'requests',
      ],
      zip_safe=False)
