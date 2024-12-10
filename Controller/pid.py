import json

class filepid:
    def save(self, data):
        try:
            with open('pid.json', 'w') as f:
                json.dump(data, f)
            return True
        except:
            return False
            
    def load(self):
        try:
            with open('pid.json', 'r') as f:
                return json.load(f)
        except:
            return {}
