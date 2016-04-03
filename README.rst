UGCAL
=====

.. image:: https://travis-ci.org/UsergroupsLT/ugcal.svg?branch=master
    :target: https://travis-ci.org/UsergroupsLT/ugcal

Tool used fetch upcoming meetups from meetup.com API and create events on
Google Calendar. Originally created to update http://usergroups.lt calendar.

How to use it?
--------------

- Create `config.json` and `client_secret.json` files by `*.example.json`.
- `$ python setup.py install`
- `$ ugcal-cli`

Todo && Wishlist
----------------

- Update existing events
- Change structure to be a real python module.
- Remove events if they are not listed on meetup.com anymore
- CLI-based config setup
