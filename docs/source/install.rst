Install ryzom
~~~~~~~~~~~~~

Installing from PyPi
--------------------

To install ryzom from PyPi, use pip with the following command in your terminal::

   pip install ryzom

If you are not in a virtualenv_, the above will fail if not executed as root,
in this case use ``install --user``::

    pip install --user ryzom

Installing from GitLab
----------------------

You can install the latest current trunk of ryzom directly from GitLab using pip_::

   pip install --user -e git+git://yourlabs.io/oss/ryzom.git@master#egg=ryzom

.. warning:: ``[dev]``, ``--user``, ``@master`` are all optional above.

Installing from source
----------------------

1. Download a copy of the code from GitHub. You may need to install git_::

       git clone https://yourlabs.io/oss/ryzom.git

2. Install the code you just downloaded using pip, assuming your current
   working directory has not changed since the previous command.::

       pip install -e ./ryzom

Build Javascript bundles using webpack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Use ``yarn`` to download required modules and build bundles.::

    cd <install dir>/js
    yarn install
    yarn start  # to build ryzom_example CRUDLFA+ demo (requires postgres db)
    yarn start2  # to build ryzom_dm2 MUI demo (uses sqlite3 db)

Create database for ryzom_example project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Install ``postgres`` on your platform. For Linux::

    sudo apt install postgresql-10

2. Create database user for the example project::

    sudo -u postgres psql -c "create user ryzom password 'ryzom';"

3. Create database for the example project::

    sudo -u postgres psql -c "create database django_ddp_test_project owner ryzom;"

Migrate database for either example project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Migrate database and start development server for the example projects::

    ryzom migrate
    ryzom runserver  # ryzom_example demo now at http://localhost:8000

    ryzom2 migrate
    ryzom2 runserver  # ryzom_dm2 demo now at http://localhost:8000

Now move on to the :doc:`tutorial`.

.. _git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
.. _pip: https://pip.pypa.io/en/stable/installing/
.. _PyPi: https://pypi.python.org/pypi
.. _virtualenv: https://virtualenv.pypa.io/
