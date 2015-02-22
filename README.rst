modoboa-amavis
==============

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
    
      # Extensions here
      # ...
      'modoboa_admin',
      'modoboa_amavis',
    )

Run the following commands to setup the database tables::

  $ cd <modoboa_instance_dir>
  $ python manage.py migrate modoboa_admin
  $ python manage.py load_initial_data
    
Finally, restart the python process running modoboa (uwsgi, gunicorn,
apache, whatever).

