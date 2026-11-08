# #41 get_user should raise when the user doesn't exist

`get_user()` returns `None` for an unknown id, and the API turns that into a 500
further down. Make it raise `UserNotFound` so the API can return a 404.
