MoYa

Juliet Tran '22 & Teo Falk '24

In implementing this project, we drew a lot of inspiration for our "base" implementation (layout template, sessions, login/logout etc.) from the Finance PSET.
The design of the website (html templates) was also inspired by finance, as we used many of the same bootstrap elements for our project. We did however make
greater use of jinja in our templates, especially jinja for loops and if statements, which were incredibly useful in terms of design, as we could return the
same template for a number of different actions.

Apart from that, we tried to implement our project as simply as possible, perhaps sacrificing some efficiency to be ensured we would have time to implement
all the features we wanted to. Most features have their own app.route. We rely heavily on SQL to provide and store information, which was very useful since we
have so many different types of information attached to every user, post, and comment. We tried to store our images in SQL as BLOBs, but were unable to
make it work the way we wanted to, which is why we opted for storing uploaded images locally in the "photos" folder, and instead storing the file name
in our SQL database. While this effectively does the same thing we wanted to do originally, it would have been cleaner and more efficient to just store
the entire file in our database.

I think one way we could have improved our program would be to make more use of GET requests, which would make it easier to switch between app.routes.
Overall we are very happy with how much we were able to implement in just over four days, and how relatively bug-free the application is for the number of
features in it. Of course there are several ways the application could be improved, and given more time we could definitely provide a more polished version
of the MoYa.