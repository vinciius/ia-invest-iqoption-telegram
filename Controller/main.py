from iqoptionapi.stable_api import IQ_Option
import time
import logging
from datetime import datetime
from .trading import IQOptionTrading
from .controlDao import selectUserById, selectConfigById

def check_iq_credentials(email, password, use_demo=True):
    """
    Verifica se as credenciais da IQ Option são válidas
    Retorna (bool, str, IQ_Option): (sucesso, mensagem, api_instance)
    """
    try:
        trader = IQOptionTrading(email, password)
        success, msg = trader.connect(use_practice=use_demo)
        
        if success:
            return True, "Login realizado com sucesso!", trader
        else:
            return False, msg, None
            
    except Exception as e:
        return False, f"Erro ao tentar conectar: {str(e)}", None

def test_binary_operation(trader, active="EURUSD", duration=1, amount=2):
    """
    Testa uma operação binária na conta demo
    Retorna (bool, str): (sucesso, mensagem)
    """
    try:
        success, msg, result = trader.make_operation(amount, active=active, duration=duration)
        
        if success:
            if result > 0:
                return True, f" Operação de teste bem sucedida! Lucro: ${result}"
            elif result < 0:
                return True, f" Operação de teste perdida. Perda: ${abs(result)}"
            else:
                return True, " Operação de teste empatada"
        else:
            return False, f" {msg}"
            
    except Exception as e:
        return False, f" Erro ao testar operação: {str(e)}"

def comand(chat_id, type_account):
    """
    Inicia o processo de operações
    """
    try:
        # Obtém dados do usuário
        ok, user_data = selectUserById(str(chat_id))
        if not ok or not user_data:
            print(f"Erro: usuário {chat_id} não encontrado")
            return False
            
        # Obtém configurações
        ok, config = selectConfigById(str(chat_id))
        if not ok or not config:
            print(f"Erro: configurações do usuário {chat_id} não encontradas")
            return False
            
        # Conecta à IQ Option
        trader = IQOptionTrading(user_data['email'], user_data['password'])
        success, msg = trader.connect(use_practice=(type_account == "PRATICA"))
        
        if not success:
            print(f"Erro ao conectar: {msg}")
            return False
            
        print("\n=== INICIANDO OPERAÇÕES ===")
        print(f"Modo: {type_account}")
        print(f"Par: {config['pair']}")
        print(f"Stop Win: ${config['stopwin']}")
        print(f"Stop Loss: ${config['stoploss']}")
        print(f"Valor entrada: ${config['value_investment']}")
        balance = trader.get_balance()
        print(f"Saldo atual: ${balance}")
        print("==========================\n")
        
        # Configura operações
        stopwin = float(config['stopwin'])
        stoploss = float(config['stoploss'])
        valor_entrada = float(config['value_investment'])
        par = config['pair']
        timeframe = 1
        
        # Loop principal
        profit = 0
        operacoes = 0
        print("Iniciando loop de operações...")
        
        while True:
            try:
                # Verifica se deve parar
                if profit >= stopwin:
                    print(f"\n🎯 Stop Win atingido!")
                    print(f"Lucro total: ${profit}")
                    print(f"Total operações: {operacoes}")
                    break
                elif profit <= -stoploss:
                    print(f"\n⛔ Stop Loss atingido!")
                    print(f"Perda total: ${abs(profit)}")
                    print(f"Total operações: {operacoes}")
                    break
                    
                # Faz uma operação
                print(f"\n>> Iniciando operação #{operacoes + 1}")
                print(f"Par: {par} | Entrada: ${valor_entrada}")
                
                success, msg, result = trader.make_operation(valor_entrada, active=par, duration=timeframe)
                operacoes += 1
                
                if success:
                    profit += result
                    if result > 0:
                        print(f"✅ WIN! +${result}")
                    elif result < 0:
                        print(f"❌ LOSS! -${abs(result)}")
                    else:
                        print("➖ EMPATE!")
                    print(f"Resultado parcial: ${profit} ({operacoes} operações)")
                else:
                    print(f"❌ Erro na operação: {msg}")
                    
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Erro no loop principal: {str(e)}")
                time.sleep(1)
                
        print("\n=== FINALIZANDO OPERAÇÕES ===")
        print(f"Resultado final: ${profit}")
        print(f"Total operações: {operacoes}")
        print("============================\n")
        return True
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        return False
