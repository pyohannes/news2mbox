news2mbox
=========

*news2mbox* fetches and stores newsgroups articles from NNTP servers for offline
reading. Articles are stored in mailboxes of the *mbox* format.

Messages are fetched cumulatively, with each subsequent call of *news2mbox*
only new articles are fetched. 


Requirements
------------

*news2mbox* requires:

 - Python 3

 - GNU make

 - fetzen (for the documentation)

 - pdflatex (for the documentation)


Installation
------------

*news2mbox* is currently used and tested only on Linux. To build and install
the program run the following:

.. code:: bash

    make
    make install

To build the documentation run:

.. code:: bash

    make doc

This will build the PDF document *doc/news2mbox.pdf* containing a detailed
description of the source code, the program features and the configuration
files.
