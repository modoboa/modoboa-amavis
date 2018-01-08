.. modoboa-amavis documentation master file, created by
   sphinx-quickstart on Sun Feb 22 14:35:42 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to modoboa-amavis's documentation!
==========================================

This plugin provides a simple management frontend for `amavisd-new
<http://www.amavis.org>`_. The supported features are:

* SQL quarantine management: available to administrators or users,
  possibility to delete or release messages
* Per domain customization (using policies): specify how amavisd-new
  will handle traffic
* Manual training of `SpamAssassin
  <http://spamassassin.apache.org/>`_ using quarantine's content

.. note::

   The per-domain policies feature only works for new
   installations. Currently, you can't use modoboa with an existing
   database (ie. with data in ``users`` and ``policies`` tables).

.. note::

   This plugin requires amavisd-new version **2.7.0** or higher. If
   you're planning to use the :ref:`selfservice`, you'll need version
   **2.8.0**.

.. note::

   ``$sql_partition_tag`` should remain undefined in ``amavisd.conf``. Modoboa
   does not support the use of ``sql_partition_tag``, setting this value can
   result in quarantined messages not showing or the wrong messages being
   released or learnt as ham/spam.

Contents:

.. toctree::
   :maxdepth: 2

   install
   setup
