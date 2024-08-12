from core.domain import DomainObject
from db import collection_users
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity


class UserSettings:
    def __init__(self, user_theme='system', theme='light', model='gpt-4o-mini', speech_model='tts-1', speech_voice='echo', speech_speed=1, google_access_token='', google_selected_details=None):
        self.user_theme = user_theme
        self.theme = theme
        self.model = model
        self.speech_model = speech_model
        self.speech_voice = speech_voice
        self.speech_speed = speech_speed
        self.google_access_token = google_access_token
        self.google_selected_details = google_selected_details


    def __str__(self):
        return f"UserSettings: {self.user_theme}, {self.theme}, {self.model}, {self.speech_model}, {self.speech_voice}, {self.speech_speed}, {self.google_access_token}, {self.google_selected_details}"
    
    def load(self, data):
        self.user_theme = data.get('user_theme', 'system')
        self.theme = data.get('theme', 'light')
        self.model = data.get('model', 'gpt-4o-mini')
        self.speech_model = data.get('speech_model', 'tts-1')
        self.speech_voice = data.get('speech_voice', 'echo')
        self.speech_speed = data.get('speech_speed', 1)
        self.google_access_token = data.get('google_access_token', '')
        self.google_selected_details = data.get('google_selected_details', None)

    def to_dict(self):
        return {
            "user_theme": self.user_theme,
            "theme": self.theme,
            "model": self.model,
            "speech_model": self.speech_model,
            "speech_voice": self.speech_voice,
            "speech_speed": self.speech_speed,
            "google_access_token": self.google_access_token,
            "google_selected_details": self.google_selected_details
        }


class User: 
    def __init__(self, domain= "", email="", name="", password="", role=None, settings=None):
        self.default_role = 'user'
        self._id = None
        self.domain = domain
        self.email = email
        self.name = name
        self.password = password # private field
        self.role = role if role else self.default_role
        self.settings = settings if settings else UserSettings()

        self.access_token = None
        self.refresh_token = None

    def __str__(self):
        return f"User: {self.domain}, {self.email}, {self.name}, {self.role}, {self.settings}"
    
    def load(self, data):
        self._id = data.get('_id', None)
        self.domain = data.get('domain')
        self.email = data.get('email')
        self.name = data.get('name')
        self.password = data.get('password')
        self.role = data.get('role', self.default_role)
        self.settings.load(data.get('settings', {}))

    def load_from_id(self, user_id):
        user = collection_users.find_one({"_id": user_id})
        if user:
            self.load(user)
            return True
        return False

    def load_current_user(self):
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return False
        return self.load_from_id(current_user_id)

    def to_dict(self):
        return {
            "domain": self.domain,
            "email": self.email,
            "name": self.name,
            "password": self.password,
            "role": self.role,
            "settings": self.settings.to_dict()
        }
    
    def save(self):
        data = self.to_dict()
        result = collection_users.insert_one(data)
        return str(result.inserted_id)
    
    def update(self):
        data = self.to_dict()
        result = collection_users.update_one({'_id': self._id}, {'$set': data})
        return result.modified_count > 0
    
    def delete(self):
        result = collection_users.delete_one({"_id": self._id})
        return result.deleted_count > 0
    

    def register(self):
        user = collection_users.find_one({"email": self.email})
        if user:
            # remove duplicate user
            collection_users.delete_one({"email": self.email})
            # return False
        self.role = self.default_role
        self._id = self.save()
        self.load_from_id(self._id)
        self.create_tokens()
        return True
    
    def login(self):
        user = collection_users.find_one({"email": self.email, "password": self.password})
        if user:
            self.load(user)
            self.create_tokens()
            return True
        return False
    
    def create_tokens(self):
        self.access_token = create_access_token(identity=str(self._id))
        self.refresh_token = create_refresh_token(identity=str(self._id))
        # self.update()
    
    def validate(self):
        """Email and password should not be empty
        Email should be unique
        Domain should be exist
        """
        validate_messages = []
        if not self.email or not self.password:
            validate_messages.append("Email and password are required")
        user = collection_users.find_one({"email": self.email})
        if user:
            # remove duplicate user
            collection_users.delete_one({"email": self.email})
            # validate_messages.append("Email is already used")
        domain = DomainObject.load(self.domain)
        if not domain:
            validate_messages.append("Domain is not found")
        return validate_messages

