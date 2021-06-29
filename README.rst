modoboa-amavis
==============

|gha| |codecov|

The `amavis <http://www.amavis.org/>`_ frontend of Modoboa.

Installation
------------

Install this extension system-wide or inside a virtual environment by
running the following command::

  $ pip install modoboa-amavis

Edit the settings.py file of your modoboa instance and add
``modoboa_amavis`` inside the ``MODOBOA_APPS`` variable like this::

    MODOBOA_APPS = (
        'modoboa',
        'modoboa.core',
        'modoboa.lib',
        'modoboa.admin',
        'modoboa.relaydomains',
        'modoboa.limits',
        'modoboa.parameters',
        # Extensions here
        # ...
        'modoboa_amavis',
    )

Then, add the following at the end of the file::

  from modoboa_amavis import settings as modoboa_amavis_settings
  modoboa_amavis_settings.apply(globals())

Run the following commands to setup the database tables::

  $ cd <modoboa_instance_dir>
  $ python manage.py migrate
  $ python manage.py collectstatic
  $ python manage.py load_initial_data

Finally, restart the python process running modoboa (uwsgi, gunicorn,
apache, whatever).

Note
----
Notice that if you dont configure amavis and its database, Modoboa
won't work. Check `docs/setup` for more information.

.. |gha| image:: https://github.com/modoboa/modoboa-amavis/actions/workflows/plugin.yml/badge.svg
   :target: https://github.com/modoboa/modoboa-amavis/actions/workflows/plugin.yml

.. |codecov| image:: https://codecov.io/gh/modoboa/modoboa-amavis/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/modoboa/modoboa-amavis
