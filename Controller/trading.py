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
            
    def get_asset_variations(self, active):
        """
        Retorna todas as variações possíveis do nome do ativo
        """
        variations = [
            active,              # EURUSD
            f"{active}-op",      # EURUSD-op
            f"{active}-OTC",     # EURUSD-OTC
            f"{active}:N"        # EURUSD:N
        ]
        return variations
        
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
            
            # Pega todas as variações do nome do ativo
            variations = self.get_asset_variations(active)
            print(f"\nVerificando variações do ativo: {variations}")
            
            # Verifica disponibilidade em diferentes modos
            print("\nVerificando disponibilidade...")
            all_open = self.api.get_all_open_time()
            
            # Debug dos tipos disponíveis
            print(f"Tipos de operação disponíveis: {list(all_open.keys())}")
            
            for type_name in all_open:
                print(f"\nAtivos disponíveis em {type_name}:")
                available = []
                for name, data in all_open[type_name].items():
                    if data['open']:
                        available.append(name)
                        # Verifica se é uma das variações que procuramos
                        if name in variations:
                            print(f"✅ Encontrado {name} disponível em {type_name}")
                            return True, (type_name, name)
                print(f"Total: {len(available)}")
                if available:
                    print("Exemplos:", available[:5])
            
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
            is_open, mode_info = self.check_asset_open(active)
            
            if not is_open:
                print(f"Ativo {active} não está disponível: {mode_info}")
                return False, f"Ativo indisponível: {mode_info}", 0
                
            # Extrai o modo e o nome correto do ativo
            mode, correct_active = mode_info
            print(f"✅ Ativo {correct_active} está disponível no modo {mode}")
            
            # Configura a operação
            if direction.lower() == "call":
                action = "buy"
            else:
                action = "sell"
                
            # Executa a operação
            try:
                print(f"\nExecutando operação {action.upper()} em {correct_active}...")
                print(f"Valor: ${amount} | Duração: {duration}m")
                
                # Força reconexão antes da operação
                self.api.check_connect()
                
                # Faz a operação
                if mode == "digital":
                    print("Executando operação digital...")
                    result = self.api.buy_digital_spot(correct_active, amount, action, duration)
                else:
                    print("Executando operação binária...")
                    try:
                        result = self.api.buy(amount, correct_active, direction, duration)
                        print(f"Retorno bruto da operação: {result}")
                        
                        # Se retornou uma tupla/lista
                        if isinstance(result, (tuple, list)):
                            # Pega apenas os dois primeiros valores
                            check = result[0] if len(result) > 0 else False
                            operation_id = result[1] if len(result) > 1 else None
                        else:
                            check = bool(result)
                            operation_id = None
                            
                    except ValueError as e:
                        print(f"ValueError ao desempacotar resultado: {str(e)}")
                        print("Tentando extrair resultado...")
                        
                        # Se der erro no desempacotamento, tenta pegar o resultado bruto
                        if isinstance(result, (tuple, list)) and len(result) > 0:
                            check = result[0]
                            operation_id = result[1] if len(result) > 1 else None
                        else:
                            check = False
                            operation_id = None
                    
                print(f"Resultado processado: check={check}, id={operation_id}")
                
                if not check or not operation_id:
                    error_msg = str(operation_id) if operation_id else "Falha desconhecida"
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
                        
                        if isinstance(result, (list, tuple)):
                            if len(result) >= 2:
                                status, win_amount = result
                                # Converte para float se for string
                                if isinstance(win_amount, str):
                                    win_amount = float(win_amount)
                                    
                                if status in ['win', 'loose']:  # Note: API retorna 'loose' ao invés de 'loss'
                                    return True, f"Operação {status}", win_amount
                            
                        # Se chegou aqui, resultado ainda não está disponível
                        time.sleep(1)
                        continue
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
