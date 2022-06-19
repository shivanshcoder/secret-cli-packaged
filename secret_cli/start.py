import os
import time
import json
from typing import Dict
from threading import Thread
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import PasswordValidator
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.shortcuts import input_dialog
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter
from .crypto import crypto


from .BaseCLI import BaseCLI
from .sync import SyncHandler
from .utils import cred_string, toggle_input
from .record import RecordApp
from .utils import toggle_input
from .exceptions import WrongPassLimit
from .listing import ListingApp

SAMPLE_CONFIG = {"creds": [{'info': {'company': 'andSons', 'email': 'gregory06@evans.info', 'username': 'john76'}, 'secret': {'password': 'L$@0ZnCa3B'}, 'id': 0}, {'info': {'company': 'LLC', 'email': 'nelliott@barnes.com', 'username': 'lindseyneal'}, 'secret': {'password': '((h%7QNfK$'}, 'id': 1}], 'config':{"config_filename": ""}}

class App:
    master_password = ""
    
    main_app = None # Handles the main tasks, like search and auto complete for everything
    view_app = None # Handles when we want to view the whole block
    list_app = None # Handles listing all the blocks after doing a search operation without single target
    edit_add_app = None # Handles when we are editing or adding a new secret to a block
    creds = None
    config = None
    """
    Start with taking master password and also MFA(later on)
    """
    def authenticate(self):
        # self.master_password = input_dialog(
        #     title="Secret-cli",
        #     text="Please enter Master Password:",
        #     password=True,
        # ).run()
        # TODO 
        # MFA_code = input_dialog(
        #     title="Secret-cli",
        #     text="Please enter Master Password:",
        #     password=True,
        # ).run()
        chances = 3
        while True:
            self.master_password = toggle_input("Please Enter Master Password: ")   
            try:
                c = crypto(self.master_password, **(self.creds))
                self.creds = json.loads(c.decrypt().to_dict()['data'])
                self.config = self.creds["config"]
                self.creds = self.creds["creds"]
                break
            except:
                chances-=1
                if chances == 0:
                    raise WrongPassLimit("Maximum Wrong Password limit reached")
                print("Wrong Password")
        
        for i,cred in enumerate(self.creds):
            cred['id'] = i
    
    def __init__(self) -> None:
        # Read the credential file
        self.creds = []
        try:
            if not self.check_configs():
                self.authenticate()
            
        except Exception as e:
            print(e)
            return
        self.auto_save_thread = Thread(target=self.auto_save, daemon=True)
        self.auto_save_thread.start()
        
        # Preprocessing for searching
        self.search_preprocessing()
        
        self.main_app = BaseCLI(self.creds, self.process_input)
        
        self.main_app.run()    
    
    def read_config(self) -> Dict:
        with open(os.path.join(self.config_folder, self.chosen_config)) as f:
            return json.loads(f.read())
        return False
            
    
    def check_configs(self)-> None:
        home = os.path.expanduser("~")
        self.config_folder = os.path.join(home, 'secret_cli')
        if not os.path.isdir(self.config_folder):
            # Config Folder doesn't exists
            os.mkdir(self.config_folder)
        available_configs = os.listdir(self.config_folder)
        if len(available_configs) == 0:
            # Create a new Password
            new_password = inquirer.secret(
                message="New password:",
                validate=PasswordValidator(length=4, number=True), # ! use the below validator later
                # validate=PasswordValidator(length=8, cap=True, special=True, number=True),
                transformer=lambda _: "[hidden]",
                long_instruction="Password require length of 8, 1 cap char, 1 special char and 1 number char.",
            ).execute()
            confirm_password = inquirer.secret(
                message="Confirm password:",
                validate=lambda text: text == new_password,
                transformer=lambda _: "[hidden]",
                long_instruction="Password require length of 8, 1 cap char, 1 special char and 1 number char.",
            ).execute()
            self.master_password = confirm_password
            self.chosen_config = f"config{(str(hash(time.time())))[2:]}.json"
            self.creds = SAMPLE_CONFIG['creds']
            self.config = SAMPLE_CONFIG['config']
            self.config['config_filename'] = self.chosen_config
            self.save_data()
            return True 
        else:
            self.chosen_config = inquirer.select(
                message="Select the Credentials File to use",
                choices= available_configs,
                cycle=True
            ).execute()
            
            with open(os.path.join(self.config_folder, self.chosen_config)) as f:
                self.creds = json.loads(f.read())
            return False
            
    def search_preprocessing(self):
        self.search_list = []
        # print(type(self.creds))
        for cred in self.creds:
            self.search_list.append(set([ f'{key}:{cred["info"][key]}' for key in cred['info'] ]))
            
    def save_data(self):
        data = {
            "creds": self.creds,
            "config": self.config
        }
        encryptedData = crypto(self.master_password, data = json.dumps(data)).encrypt().to_dict()
        with open(os.path.join(self.config_folder, self.chosen_config), "w") as file:
            file.write(json.dumps(encryptedData))
            
    def auto_save(self):
        while True:
            # Save every 10 seconds
            time.sleep(10)
            self.save_data()
            
            
    def search_result(self, processed_input):
        clear()
        args = processed_input['arg']
        search_filter = [ text for text in processed_input['arg'] if ':' in text]
        search_results = []
        for i,search in enumerate(self.search_list):
            match_found = True
            for r in search_filter:
                if r not in search:
                    match_found = False
            if match_found:
                search_results.append((cred_string(self.creds[i]), ",".join([self.creds[i]['info'][k] for k in (self.creds[i]['info'])])))
                
        # Check count and if there exists a sub command
        if len(search_results) == 0:
            print("No Results Found!")
            return
        app = ListingApp(search_results)
        chosen = app.run()
        if chosen == None:
            return None
        chosen_id = json.loads(chosen[0])['id']
        return chosen_id
    
    def process_input(self, processed_input):
        if processed_input['type'] == "sync":
            sh = SyncHandler(self, processed_input['arg'])
        if processed_input['type'] == "save":
            self.save_data()  
        elif processed_input['type'] == "search":
            chosen_id = self.search_result(processed_input)
            if chosen_id != None:
                app = RecordApp(self.creds[chosen_id])
                app.run()
        

def main():
    try:  
        app = App()
    except (WrongPassLimit):
        print("Max Limit reached for Wrong Passwords, Try Again")

if __name__ == "__main__":
    exit(main())
