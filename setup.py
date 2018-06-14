from setuptools import setup

setup(name='confhttpproxy',
      version='0.0.0',
      description='Python interface for jupyter/configurable-http-proxy',
      url='http://github.com/gigantum/confhttpproxy',
      author='Bill',
      author_email='hello@gigantum.io',
      license='MIT',
      packages=['confhttpproxy'],
      install_requires=[
          'pytest',
          'requests'
      ],
      zip_safe=False)
