import json

class file:
    def __init__(self, chat_id):
        self.chat_id = str(chat_id)
        
    def save(self, data):
        try:
            with open(f'settings_{self.chat_id}.json', 'w') as f:
                json.dump(data, f)
            return True
        except:
            return False
            
    def load(self):
        try:
            with open(f'settings_{self.chat_id}.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'stopwin': 0,
                'stoploss': 0,
                'payout': 0,
                'pair': '',
                'factor_gale': 0,
                'amount_gale': 0,
                'value_investment': 0
            }
    
    @staticmethod
    def get_value_by_id(chat_id):
        try:
            with open(f'settings_{chat_id}.json', 'r') as f:
                return json.load(f)
        except:
            return None

    @staticmethod
    def set_value_id(chat_id, value):
        try:
            with open(f'settings_{chat_id}.json', 'w') as f:
                json.dump({'running': value}, f)
            return True
        except:
            return False
