import json
from datetime import datetime

def connectDao():
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
        return data
    except:
        return {}

def saveDao(data):
    with open('data.json', 'w') as f:
        json.dump(data, f)

def saveUser(user_id, email, password, date_validade):
    """
    Salva ou atualiza os dados do usuário
    """
    try:
        data = connectDao()
        # Se já existe configuração, mantém ela
        existing_config = {}
        if str(user_id) in data:
            existing_config = data[str(user_id)].get('config', {})
            
        data[str(user_id)] = {
            'email': email,
            'password': password,
            'date_validade': date_validade,
            'active': True,
            'config': existing_config or {
                'stopwin': '0',
                'stoploss': '0',
                'payout': '0',
                'pair': 'EURUSD',
                'factor_gale': '2',
                'amount_gale': '2',
                'value_investment': '2'
            }
        }
        saveDao(data)
        return True
    except Exception as e:
        print(f"Erro ao salvar usuário: {str(e)}")
        return False

def addUser(email, date):
    data = connectDao()
    data[email] = {
        'date': date,
        'active': True,
        'config': {
            'stopwin': 0,
            'stoploss': 0,
            'payout': 0,
            'pair': '',
            'factor_gale': 0,
            'amount_gale': 0,
            'value_investment': 0
        }
    }
    saveDao(data)

def checkUser(email):
    data = connectDao()
    if email in data:
        user = data[email]
        if user['active']:
            date_str = user['date']
            expiry_date = datetime.strptime(date_str, '%Y-%m-%d')
            if datetime.now() <= expiry_date:
                return True
    return False

def removeUser(email):
    data = connectDao()
    if email in data:
        del data[email]
        saveDao(data)
        return True
    return False

def selectUserById(user_id):
    """
    Retorna os dados do usuário pelo ID
    Retorna (bool, dict): (sucesso, dados do usuário)
    """
    try:
        data = connectDao()
        if str(user_id) in data:
            return True, data[str(user_id)]
        return False, None
    except Exception as e:
        print(f"Erro ao buscar usuário: {str(e)}")
        return False, None

def selectConfigById(user_id):
    """
    Retorna as configurações do usuário pelo ID
    Retorna (bool, dict): (sucesso, configurações)
    """
    try:
        data = connectDao()
        if str(user_id) in data:
            user = data[str(user_id)]
            return True, user.get('config', {})
        return False, None
    except Exception as e:
        print(f"Erro ao buscar configurações: {str(e)}")
        return False, None

def saveConfigUser(user_id, stopwin, stoploss, payout, pair, factor_gale, amount_gale, value_investment):
    """
    Salva ou atualiza as configurações do usuário
    """
    try:
        data = connectDao()
        if str(user_id) not in data:
            return False
            
        # Atualiza apenas as configurações
        data[str(user_id)]['config'] = {
            'stopwin': str(stopwin),
            'stoploss': str(stoploss),
            'payout': str(payout),
            'pair': str(pair),
            'factor_gale': str(factor_gale),
            'amount_gale': str(amount_gale),
            'value_investment': str(value_investment)
        }
        saveDao(data)
        return True
    except Exception as e:
        print(f"Erro ao salvar configurações: {str(e)}")
        return False
