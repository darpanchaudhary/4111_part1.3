The postegreSQL account is psql -U kq2129 -h 35.196.90.148 -d proj1part2
The URL is https://35.196.81.152/8111

We've implemented all parts of our original proposal. We have a chess database which 
contains chess tournaments, players, organizers, games, moves, and positions. End
users can interact with our database by inserting, deleting, and querying from these
relations.

They can look up games of their favorite players, add new games, view their win percentage,
go through their moves in order, look at which tournaments they've played in, and more.

They can see how many games were played in each tournament, add their own tournaments, 
create their own organizers. They can see how many tournaments an organizer has organized.
They can even insert their games in the standard PGN format for portable chess notation 
(this is stored differently internally, but they are not exposed to this).

 
The application begins with a couple of boxes detailing the relations the user needs to see
(Tournaments, Organizers, Players, Games). Clicking a box redirects to a page which allows
insertion, deletion, and queries. These are all simple to use as they just require filling
in fields and clicking submit. These are converted into SQL queries under-the-hood. After
clicking submit, the user must go back from the success page and reload the page to continue
use.


 
