from setuptools import setup


def readme():
    with open('README.md') as f:
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
      entry_points={
          'console_scripts': ['ugcal-cli=ugcal.ugcal:main']
      },
      zip_safe=False)
