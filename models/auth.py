from db import collection_users


def auth_login(request):
    # Get the email and password from the request
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    # Check if the email and password are valid
    if not email or not password:
        return {"error": "Invalid email or password"}
    user = collection_users.find_one({"email": email, "password": password})
    if user:
        print(user)
        token = generate_token(user['_id'])
        return token
    else:
        return {"error": "Invalid email or password"}

def generate_token(user_id):
    # Implement the logic to generate a token based on the user_id
    # Return the generated token
    # pass
    return 'asldfjasoeru9qworj-o123543nasdfjasldfj'

def is_valid_token(token):
    # Implement the logic to check if a token is valid
    # Return True if the token is valid, False otherwise
    pass


def get_token(username, password):
    # Retrieve user from the database based on username and password
    user = collection_users.find_one({'username': username, 'password': password})
    if user:
        # Generate and return a token for the user
        token = generate_token(user['_id'])
        return token
    else:
        return None

def refresh_token(token):
    # Check if the token is valid and not expired
    if is_valid_token(token):
        # Refresh the token and return the updated token
        refreshed_token = generate_token(token)
        return refreshed_token
    else:
        return None

def login(username, password):
    # Retrieve user from the database based on username and password
    user = collection_users.find_one({'username': username, 'password': password})
    if user:
        # Generate and return a token for the user
        token = generate_token(user['_id'])
        return token
    else:
        return None

def register(username, password):
    # Check if the username is already taken
    if collection_users.find_one({'username': username}):
        return None
    else:
        # Create a new user in the database
        user = {'username': username, 'password': password}
        user_id = collection_users.insert_one(user).inserted_id
        # Generate and return a token for the new user
        token = generate_token(user_id)
        return token