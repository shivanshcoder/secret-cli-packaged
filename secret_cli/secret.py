import json

from .utils import *
from .crypto import *

class secret:
    def __init__(self) -> None:
        self.data = {}
        pass
    
    def to_json(self) -> str:
        return json.dumps(self.data)
    
    def add_update_property(self, key, val):
        self.data['info'][key] = val
        pass
    
    def add_update_secret(self, key, val):
        self.data['secret'][key] = val
        pass


class secret_manager:
    
    def __init__(self) -> None:
        self.storage_path = "~/"
        self.master_password = "MyPass"
        
    def read_vault(self):
        
        file_path = os.path.join(self.storage_path, "vault.json")

        try:
            with open(file_path, "r") as f:
                data = f.read()
                data_dict = json.loads(data)
        except:
            data_dict = {}


        decrypted_data = crypto(self.master_password, **data_dict).decrypt().to_dict()
        """decrypted_data of type dict

            {
                'salt':the_salt,
                'data':decrypted_data
            }
        """

        return json.loads(decrypted_data['data'])
        self.vault_dict = json.loads(decrypted_data['data'])
        print(self.vault_dict)
    
    pass

    def check_pass_validity(self):
        
        pass

if __name__ == "__main__":
    if True:
        creds = []

        with open("user_cred.json", "r") as file:
            creds = json.loads(file.read())
            
        encryptedData = crypto("MyPass", json.dumps(creds)).encrypt().to_dict()
        with open("encrypted_data.json", "w") as file:
            file.write(json.dumps(encryptedData))
    else:
        with open("encrypted_data.json", "r") as file:
            data = file.read()
            
        c = crypto("MyPass", **json.loads(data))
        while True:
            inn = input("what to do")
            c.refresh_counter()
            if (inn == "exit"):
                (c.clean())
                break
            datas = c.decrypt().to_dict() 
            
            print(json.loads(datas['data'])[10])
        
        pass