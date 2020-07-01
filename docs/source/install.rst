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

   pip install --user -e git+git://yourlabs.io/oss/ryzom.git@master#egg=ryzom[dev]

.. warning:: ``[dev]`` (to install channels and client-side rendering),
             ``--user`` (to install a local version), and
             ``@master`` are all optional above.

Installing from source
----------------------

1. Download a copy of the code from GitHub. You may need to install git_::

       git clone https://yourlabs.io/oss/ryzom.git

2. Install the code you just downloaded using pip, assuming your current
   working directory has not changed since the previous command.::

       pip install -e ./ryzom

Create database for the ryzom_example project in the [dev] install
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Install ``postgres`` on your platform. For Linux::

       sudo apt install postgresql-10

2. Create database user for the example project::

       sudo -u postgres psql -c "create user ryzom password 'ryzom';"

3. Create database for the example project::

       sudo -u postgres psql -c "create database django_ddp_test_project owner ryzom;"

4. Migrate database and start development server for the example project::

       ryzom migrate
       ryzom runserver  # CRUDLFA+ demo available at http://localhost:8000
	   # Client-side rendering demo at http://localhost:8000/todos

Known issues
~~~~~~~~~~~~

In CRUDLFA+, materialise CSS is imported, which hides standard
checkboxes. MUICSS doesn't style checkboxes by default, so this rule needs to
be disabled for the example (until materialise is removed from CRUDLFA+). 

[type="checkbox"]:not(:checked), [type="checkbox"]:checked {
    position: absolute;
    opacity: 0;  # TODO: This materialise rule hides MUI checkboxes.
    pointer-events: none;
}


Move on to the :doc:`tutorial`.

.. _git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
.. _pip: https://pip.pypa.io/en/stable/installing/
.. _PyPi: https://pypi.python.org/pypi
.. _virtualenv: https://virtualenv.pypa.io/
