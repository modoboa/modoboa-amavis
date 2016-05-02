modoboa-amavis
==============

|landscape|

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
    
        # Extensions here
        # ...
        'modoboa_amavis',
    )

Then, add the following at the end of the file::

  from modoboa_amavis.settings import *      

Run the following commands to setup the database tables::

  $ cd <modoboa_instance_dir>
  $ python manage.py migrate
  $ python manage.py load_initial_data
    
Finally, restart the python process running modoboa (uwsgi, gunicorn,
apache, whatever).

.. |landscape| image:: https://landscape.io/github/modoboa/modoboa-amavis/master/landscape.svg?style=flat
   :target: https://landscape.io/github/modoboa/modoboa-amavis/master
   :alt: Code Health
