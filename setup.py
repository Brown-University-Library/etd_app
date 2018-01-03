from setuptools import setup

setup(name='bdr-etd-app',
      version='0.5',
      description='App for storing and working with dissertations',
      author='Brown University Libraries',
      author_email='bdr@brown.edu',
      url='https://github.com/Brown-University-Library/etd_app',
      packages=[str('etd_app')], # https://bugs.python.org/issue13943
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'Django>=1.11,<2.0a1',
          'django-crispy-forms==1.6.0',
          'django-model-utils==2.5',
          'django-import-export==0.5.0',
          'bdrxml==0.8',
          'django-shibboleth-remoteuser==0.8',
          'django-bulstyle==1.3',
          'requests==2.18.4',
      ],
      dependency_links=[
          'https://github.com/Brown-University-Library/bdrxml/archive/v0.8.zip#egg=bdrxml-0.8',
          'https://github.com/Brown-University-Library/django-shibboleth-remoteuser/archive/v0.8.zip#egg=django-shibboleth-remoteuser-0.8',
          'https://github.com/Brown-University-Library/django-bulstyle/archive/v1.3.zip#egg=django-bulstyle-1.3',
      ],
     )
