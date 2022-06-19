
import os
import re
import random
import requests
import json
import string

import pyperclip
import qrcode

from copy import deepcopy
from typing import List
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import NumberValidator, PasswordValidator

SERVER_URL = "http://localhost:5000"

class SyncHandler:
    
    """Connect Client to our server
    
        @return [bool]: whether we have successfully connected client to server or not  
    """
    def connect_device(self)  -> bool:
        print("Please Visit the following Link, a code will be displayed.")
        print("That Code needs to be entered here later")
        
        qr = qrcode.QRCode()
        # ! Later use something else than random
        special_code = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        link = f"{SERVER_URL}/add_device/{special_code}"
        
        pyperclip.copy(link)
        print("Link has aslo been copied into clipboard")
        
        qr.add_data(link)
        qr.make()
        qr.print_ascii(tty=True, invert=True)
        
        input("Press Enter when ready to proceed")
        
        chances = 3
        
        while True:
            device_code = inquirer.text(
                message="Enter the Device Code",
                validate= lambda x: re.match('^([a-zA-z0-9]{6})$',x)
            ).execute()
            
            mfa_code = inquirer.text(
                message="Enter your MFA OTP",
                validate= lambda x: re.match('^([0-9]{6})$',x)
            ).execute()
        
            url = f"{SERVER_URL}/add_device/{special_code}"
            req = requests.post(url, json={
                'code': device_code,
                'mfa_code': mfa_code
            }) 
            
            req_data = json.loads(req.text)
            
            if req_data.get("msg", "Failed") == "Success":
                self.app.config ={ **req_data['config'], **self.app.config }
                return True
            
            chances -= 1
            
            
            print("\nVerification Failed")
            print("Either Device or MFA code is wrong")
            
            if chances == 0:
                print("\nAdd device Failed\n")
                print("Press enter to get back to cli")
                input()
                break
            
        return False
        
    def data_pull(self):
        url = f'{SERVER_URL}/getListing'
        
        req = requests.post(url, json={
            "config": self.app.config # Google auth, _id etc
        })
        
        req_data = json.loads(req.text)
        chosen = inquirer.select(
            "You have following config available in drive, Please choose one to pull",
            choices=[Choice((c[0], c[1]), c[1]) for c in req_data['listing']]
        ).execute()
        
        app_config = deepcopy(self.app.config)
        app_config['config_fileid'] = chosen[0]
        app_config['config_filename'] = chosen[1]
        
        url = f'{SERVER_URL}/get'
        req = requests.post(url, json={
            "config": app_config # Google auth, _id etc
        })
        
        
        req_data = json.loads(req.text)
        
        with open(os.path.join(self.app.config_folder, chosen[1]), "w") as file:
            file.write(json.dumps(req_data))
        
    
    def data_push(self):
        url = f'{SERVER_URL}/upload'
        chances = 3
        
        while True:
            mfa_code = inquirer.text(
                message="Enter your MFA OTP",
                validate= lambda x: re.match('^([0-9]{6})$',x)
            ).execute()
            
            config_data = self.app.read_config()
            
            req = requests.post(url, json={
                "mfa_code":mfa_code,
                "config_data": (config_data), # The encrpyted auth file
                "config": (self.app.config) # Google auth, _id etc
            })
            
            req_data = json.loads(req.text)
            
            print(req_data)
            if req_data.get("msg", "Failed") == "Success":
                self.app.config['config_fileid'] = req_data['fileid']
                self.app.save_data()
                return
            
            chances-=1
            print("\nIncorrect MFA")
            
            if chances == 0:
                print("\MFA Incorrect limit reached\n")
                print("Press enter to get back to cli")
                input()
                break
            
            
        pass
    
    def __init__(self, app, input_text:List[str]) -> None:
        self.app = app
        # self.connect_device()
        if 'google_auth' not in self.app.config:
            ans = inquirer.confirm("You have not added this device using google, Do you want to proceed to add this device?")
            if not ans:
                # Go back
                return
            
            if not self.connect_device():
                # Connecting failed, return back
                return
            
            self.app.save_data()
            
            
        if input_text[-1] == "push":
            self.data_push()
        elif input_text[-1] == "pull":
            self.data_pull()
                
if __name__ =="__main__":
    s = SyncHandler("asd", [])
    