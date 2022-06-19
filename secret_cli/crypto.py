import base64
import json
import os
import time
import cryptography

from threading import Thread
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken


# Returns a string representation of a salt
def generate_salt(size=16):
    """Returns a string representation of a salt

    Args:
        size (int, optional): Random bytes size. Defaults to 16.

    Returns:
        string: String representation of random bytes
    """
    return base64.b64encode(os.urandom(size)).decode()

class InvalidKeyException(Exception):
    pass

class crypto:
    """Cryptography class for Encrypting and Decrypting text
    """

    def __init__(self, pass_phrase, data, salt=generate_salt(), auto_lock = True):
        """initializes the crypto class

        Args:
            pass_phrase (str): the password for encrypting or decrypting
            data (str): the data we want to decrypt or encrypt
            salt (str, optional): string representation of a salt we want to use for creating key. Defaults to generate_salt().
        """
        self.auto_lock = auto_lock
        self.data = str(data)
        self.salt = salt
        self.pass_phrase = pass_phrase
        
        self.die = False
        self.valid_key = True
        self.__max_counter = 20
        self.refresh_counter()

    def create_key(self) -> bytes:
        """creates key encryption

        Returns:
            bytes: key in form of bytes
        """
        
        # Taken from the website itse
        # https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=base64.b64decode(self.salt),
            iterations=10000
        )

        key = base64.urlsafe_b64encode(kdf.derive(self.pass_phrase.encode()))

        return key    


    def encrypt(self) -> "crypto":
        """Encrypts the Data
        """
        # if self.encrypt_status == True:
        #     return
        if not self.valid_key:
            raise InvalidKeyException("Invalid PassPhrase")

        key = self.create_key()
        f = Fernet(key)
        self.data = f.encrypt(self.data.encode()).decode()
        # self.encrypt_level+=1
        # self.encrypt_status = True
        return self

    def decrypt(self) -> "crypto":
        """Decrypts the data
        """
        # if self.encrypt_status == False:
        #     return
        if not self.valid_key:
            raise InvalidKeyException("Invalid PassPhrase")
        # if self.encrypt_level <= 0:
        #     return self
        
        key = self.create_key()

        try:
            f = Fernet(key)
            self.data = f.decrypt(self.data.encode()).decode()
        except InvalidToken:
            return self 
        except:
            raise InvalidKeyException("Invalid PassPhrase")
        # self.encrypt_level-=1
        # self.encrypt_status = False
        return self

    def countdown(self) -> None:
        """
        Will run in separate thread and after some time, reset the pass_phrase and encrypt back the data
        """
        while self.counter > 0:
            time.sleep(1)
            self.counter-=1
            if self.die == True:
                print("DIEE")
                return
        self.encrypt()
        self.valid_key=False
        self.pass_phrase = ""
            
    def update_pass_phrase(self, pass_phrase) -> None:
        """
        Will run after we have run down our countdown and we wish to again use the data, need to re enter password for encryption or decryption

        Args:
            pass_phrase (str): the password for encryption or decryption of the data
        """
        self.pass_phrase = pass_phrase
        self.valid_key = True
        self.refresh_counter()

    def refresh_counter(self) -> None:
        """
            Refreshes the reset counter to start, should be used to when the user is interacting so that password doesn't reset while using it. Everytime user interacts, we can 
        """
        self.counter = self.__max_counter
        
        if not self.auto_lock:
            # If we don't want auto_lock mechanism, we can skip the rest steps 
            return
        if hasattr(self, 'pass_watcher_thread') : 
            if self.pass_watcher_thread.is_alive():
                return
        self.pass_watcher_thread = Thread(target=self.countdown, daemon=True)
        self.pass_watcher_thread.start()

    def __str__(self) -> str:
        return json.dumps(self.to_dict())

    def to_dict(self) -> dict:
        return {
            'salt':self.salt,
            'data':self.data
        }
