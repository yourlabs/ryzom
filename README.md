# ryzom

Meteor-ish Django responsive front-end

Dependencies:
  * django 2.1
  * django_channels
  * channels_redis
  * redis-server (up and running)
  * psycopg2 (up and running with database and user)

Install `ryzom`:

    pip install git+https://yourlabs.io/oss/ryzom.git

Run the example project server:

    ryzom runserver

What next?

OK/ Documentation for sure.
OK/ Automatic websocket reconnection and page reloading on success
Attach javascript events into forms and formfields with basic AST thanks to transcrypt

A tutorial

OK/ Authentication:
  - Without authentication and user specific filtering, it will remain a toy, a nice toy, but just a toy
  - With authentication, publishing can filter output by user and that will be great!
  - With authentication AND roles, it will become something really usable

OK/ Server Side Rendering:
  - the first HTTP request should return a full HTML page
  - all links should be 'a' tag that have no effect on current location

OK/ Change the way methods works, maybe by importing a dict and assigning funcptr to method name

Error handling: It won't ever be stable enough without good error reporting.

Pagination: Very important too (maybe it could be implemented through subscriptions queries?)

Transcrypt: Would be nice to avoid switching to JS.

(S)CSS components?
  - We could make an SCSS-like class to be inherited in components? Seems like a good idea.
