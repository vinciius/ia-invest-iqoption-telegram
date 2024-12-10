from iqoptionapi.stable_api import IQ_Option
import time
from datetime import datetime
import json

class IQOptionTrading:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.api = None
        self.connected = False
        
    def connect(self, use_practice=True):
        """
        Conecta à IQ Option
        Retorna (bool, str): (sucesso, mensagem)
        """
        try:
            print("\n=== Conectando à IQ Option ===")
            print(f"Email: {self.email}")
            
            self.api = IQ_Option(self.email, self.password)
            status, reason = self.api.connect()
            
            if status:
                # Força reconexão para garantir
                print("Reconectando para garantir...")
                self.api.connect()
                
                # Verifica o tipo de conta atual
                balance_type = self.api.get_balance_mode()
                print(f"Tipo de conta atual: {balance_type}")
                
                # Pega os saldos
                practice = self.api.get_balance()
                self.api.change_balance('REAL')
                real = self.api.get_balance()
                print(f"Saldo REAL: ${real}")
                print(f"Saldo PRACTICE: ${practice}")
                
                # Muda o tipo de conta
                if use_practice:
                    print("Mudando para conta PRACTICE")
                    self.api.change_balance('PRACTICE')
                else:
                    print("Mudando para conta REAL")
                    self.api.change_balance('REAL')
                    
                # Verifica novamente o tipo de conta
                balance_type = self.api.get_balance_mode()
                print(f"Tipo de conta após mudança: {balance_type}")
                
                # Verifica o status da conexão websocket
                check = self.api.check_connect()
                print(f"Status da conexão websocket: {'Conectado' if check else 'Desconectado'}")
                
                self.connected = True
                return True, "Conectado com sucesso!"
            else:
                return False, f"Falha ao conectar: {reason}"
                
        except Exception as e:
            return False, f"Erro ao conectar: {str(e)}"
            
    def check_connection(self):
        """
        Verifica se está conectado e reconecta se necessário
        """
        try:
            if not self.api or not self.connected:
                return self.connect()
            
            if not self.api.check_connect():
                return self.connect()
                
            return True, "Conectado"
        except:
            return self.connect()
            
    def get_available_assets(self):
        """
        Retorna uma lista de ativos disponíveis para operar
        """
        try:
            # Força reconexão
            self.check_connection()
            
            # Atualiza lista de ativos
            print("Atualizando lista de ativos...")
            self.api.update_ACTIVES_OPCODE()
            
            # Verifica quais estão abertos
            print("\nVerificando ativos disponíveis...")
            all_assets = self.api.get_all_open_time()
            available = []
            
            # Tipos de ativos para verificar
            asset_types = ['binary', 'digital', 'turbo']
            
            print("\nAtivos disponíveis:")
            for asset_type in asset_types:
                if asset_type in all_assets:
                    print(f"\n{asset_type.upper()}:")
                    for asset_name, data in all_assets[asset_type].items():
                        is_open = data['open']
                        if is_open:
                            if asset_name not in available:
                                available.append(asset_name)
                            print(f"✅ {asset_name}")
                        else:
                            print(f"❌ {asset_name} (fechado)")
                            
            if not available:
                print("⚠️ Nenhum ativo disponível no momento!")
            else:
                print(f"\nTotal de ativos disponíveis: {len(available)}")
            
            return available
            
        except Exception as e:
            print(f"Erro ao listar ativos: {str(e)}")
            return []
            
    def check_asset_open(self, active):
        """
        Verifica se um ativo está aberto para operar
        """
        try:
            # Força reconexão e atualização
            self.check_connection()
            
            print("\n=== Verificando API ===")
            
            # Verifica conexão websocket
            check = self.api.check_connect()
            print(f"Status da conexão websocket: {'Conectado' if check else 'Desconectado'}")
            
            # Verifica tipo de conta
            balance_type = self.api.get_balance_mode()
            print(f"Tipo de conta atual: {balance_type}")
            
            # Atualiza lista de ativos
            print("\nAtualizando lista de ativos...")
            self.api.update_ACTIVES_OPCODE()
            
            # Verifica se o ativo existe
            print("Obtendo lista de ativos...")
            actives = self.api.get_all_ACTIVES_OPCODE()
            print(f"Total de ativos encontrados: {len(actives)}")
            
            if active not in actives:
                return False, "Ativo não encontrado"
                
            # Verifica disponibilidade em diferentes modos
            print("\nVerificando disponibilidade...")
            all_open = self.api.get_all_open_time()
            
            # Debug dos tipos disponíveis
            print(f"Tipos de operação disponíveis: {list(all_open.keys())}")
            
            for type_name in all_open:
                print(f"\nAtivos disponíveis em {type_name}:")
                available = [name for name, data in all_open[type_name].items() if data['open']]
                print(f"Total: {len(available)}")
                if available:
                    print("Exemplos:", available[:5])
            
            # Verifica digital
            if 'digital' in all_open and active in all_open['digital']:
                if all_open['digital'][active]['open']:
                    return True, "digital"
                    
            # Verifica binário
            if 'binary' in all_open and active in all_open['binary']:
                if all_open['binary'][active]['open']:
                    return True, "binary"
                    
            # Verifica turbo
            if 'turbo' in all_open and active in all_open['turbo']:
                if all_open['turbo'][active]['open']:
                    return True, "turbo"
                    
            return False, "Ativo fechado em todos os modos"
            
        except Exception as e:
            return False, f"Erro ao verificar ativo: {str(e)}"
            
    def make_operation(self, amount, active="EURUSD", direction="call", duration=1):
        """
        Faz uma operação
        Retorna (bool, str, float): (sucesso, mensagem, resultado)
        """
        try:
            # Força reconexão
            success, msg = self.check_connection()
            if not success:
                return False, msg, 0
                
            # Verifica se o ativo está disponível
            print(f"\nVerificando disponibilidade do ativo {active}...")
            is_open, mode = self.check_asset_open(active)
            
            if not is_open:
                print(f"Ativo {active} não está disponível: {mode}")
                return False, f"Ativo indisponível: {mode}", 0
                
            print(f"✅ Ativo {active} está disponível no modo {mode}")
            
            # Configura a operação
            if direction.lower() == "call":
                action = "buy"
            else:
                action = "sell"
                
            # Tenta a operação no modo disponível
            try:
                print(f"\nExecutando operação {action.upper()} em {active}...")
                print(f"Valor: ${amount} | Duração: {duration}m")
                
                # Força reconexão antes da operação
                self.api.check_connect()
                
                # Executa a operação
                if mode == "digital":
                    print("Tentando operação digital...")
                    result = self.api.buy_digital_spot(active, amount, action, duration)
                else:
                    print("Tentando operação binária...")
                    result = self.api.buy(amount, active, direction, duration)
                
                # Trata o retorno
                if isinstance(result, (tuple, list)):
                    if len(result) >= 2:
                        check, operation_id = result
                    else:
                        check, operation_id = result[0], None
                else:
                    check, operation_id = result, None
                    
                print(f"Retorno da operação: check={check}, id={operation_id}")
                
                if not check or not operation_id or isinstance(operation_id, str):
                    error_msg = operation_id if isinstance(operation_id, str) else "Falha desconhecida"
                    return False, f"Falha na operação: {error_msg}", 0
                    
                print(f"✅ Operação iniciada com sucesso. ID: {operation_id}")
                
                # Espera o resultado
                start_time = time.time()
                timeout = duration * 60 + 5  # Duração + 5 segundos de margem
                
                while time.time() - start_time < timeout:
                    try:
                        print(f"Verificando resultado da operação {operation_id}...")
                        if mode == "digital":
                            result = self.api.check_win_digital_v2(operation_id)
                        else:
                            result = self.api.check_win_v4(operation_id)
                            
                        print(f"Resultado bruto: {result}")
                        
                        if isinstance(result, (list, tuple)) and len(result) >= 1:
                            win_amount = result[0]
                            if win_amount > 0:
                                return True, "Operação vencedora!", win_amount
                            elif win_amount < 0:
                                return True, "Operação perdedora", win_amount
                            else:
                                return True, "Operação empatada", 0
                    except Exception as e:
                        print(f"Erro ao verificar resultado: {str(e)}")
                    time.sleep(1)
                    
                return False, "Timeout ao esperar resultado", 0
                
            except Exception as e:
                print(f"Erro na operação: {str(e)}")
                return False, f"Erro ao executar operação: {str(e)}", 0
            
        except Exception as e:
            return False, f"Erro na operação: {str(e)}", 0

    def get_balance(self):
        """
        Retorna o saldo atual
        """
        try:
            success, msg = self.check_connection()
            if not success:
                return 0
                
            return self.api.get_balance()
        except:
            return 0
