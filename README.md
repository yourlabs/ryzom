# pyfront

Meteorish django responsive frontend

you first need to install:
- django 2.1
- django_channels
- channels_redis
- redis-server (up and running)

then juste run ./manage.py runserver from the root directory of this project

What to do next?

OK/ Documentation for sure.
OK/ Automatic websocket reconnection and page reloading on success

A tutorial

OK/ Authentication:
  - Without authentication and user specific filtering, it will remain a toy, a nice toy, but just a toy
  - With authentication, publishing can filter output by user and that will be great!
  - With authentication AND roles, it will become something really usable

Server Side Rendering:
  - the first HTTP request should return a full HTML page
  - all links should be 'a' tag that have no effect on current location

OK/ Change the way methods works, maybe by importing a dict and assigning funcptr to method name

Errors handling: It won't ever be stable enough without good errors

Pagination: Very important too (maybe it could be implemented through subscriptions queries?)

Transcrypt would be nice to avoid switching to JS..

(S)CSS components?
  - We could make scss-like class to be inherited in components? Seems like a good idea.
