from multiprocessing import Process
from iqoptionapi.constants import ACTIVESSC
from Controller.controlDao import (
    connectDao, checkUser, selectUserById, 
    selectConfigById, saveConfigUser, removeUser,
    addUser, saveUser
)
from Controller.forms import FormConfig, FormDeleteC, FormGo, FormLogin, FormUpdateC
from Controller.main import comand, check_iq_credentials, test_binary_operation
from Controller.message import controlMessage
from aiogram.dispatcher import FSMContext
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.executor import start_polling 
from datetime import datetime, timedelta
from dotenv import load_dotenv
from nav import mainMenu
from Controller.pid import filepid
import os,logging, pytz
logging.basicConfig(level=logging.INFO)
load_dotenv(".env.development.local")
bot = Bot(token=str(os.environ.get("API_TOKEN")))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
user_processes = {}
# Função para iniciar o processo e armazenar o objeto do processo no dicionário
def start_process(chat_id, type_account):
    try:
        # Verifica se já existe um processo rodando
        if chat_id in user_processes:
            raise Exception("Já existe um processo de operações rodando")
            
        # Cria e inicia o processo
        process = Process(target=comand, args=(chat_id, type_account), daemon=True)
        process.start()
        
        # Armazena o processo
        user_processes[chat_id] = process
        return True
        
    except Exception as e:
        raise Exception(f"Erro ao iniciar processo: {str(e)}")

def stop_process(chat_id):
		if chat_id in user_processes:
			process = user_processes[chat_id]
			process.terminate()
			process.join()
			del user_processes[chat_id]
			return True
		return False
	
class MyMiddleware(BaseMiddleware):
			async def on_pre_process_message(self, message: types.Message, data: dict):
				try:
					
					if str(message.chat.id) == os.environ.get("ID_ADMIN"):
						return
					if message.text == '/start':
						
						isOk, _ = selectUserById(message.chat.id)
						if isOk == False:
							# Caso o usuário não exista no banco, vamos cadastrá-lo com validade para o ano 2000
							email = "usuario@example.com"  # Substitua pelo email do usuário
							senha = "senha123"  # Substitua pela senha do usuário
							saveUser(str(message.chat.id), email, senha, '2000-07-06')
						else:	
							
							isOk = checkUser(str(message.chat.id))
							if isOk:
								return
							else:
								await message.answer("Desculpe, você não tem permissão, verifique com o suporte. Seu pagamento ou registro.")
								raise CancelHandler()
					else:
						isOk = checkUser(str(message.chat.id))
						if isOk:
							return
						else:
							await message.answer("Desculpe, você não tem permissão, verifique com o suporte. Seu pagamento ou registro.")
							raise CancelHandler()
				except ValueError:
					# Caso ocorra um erro ao converter a data de validade do usuário em um objeto de data,
					# envia uma mensagem de erro para o usuário
					await message.answer("Desculpe, houve um erro na validação do usuário. Por favor, entre em contato com o suporte.")
					raise CancelHandler()
		
@dp.message_handler(commands='start')
async def command_start(message: types.Message):
		await message.reply('Olá, escolha uma opção!',reply_markup = mainMenu)
#######################LOGIN##############################################################################
@dp.message_handler(commands='login')
async def cmd_login(message: types.Message):
		await FormLogin.email.set()
		await message.reply("Oi, qual seu email de acesso à corretora?")
@dp.message_handler(state=FormLogin.email)
async def process_email(message: types.Message, state: FSMContext):
		async with state.proxy() as data:
			data['email'] = message.text
		await FormLogin.next()
		await message.reply("Isso aí {0}, agora preciso da sua senha para que eu possa me conectar à sua conta.".format(message.chat.first_name))
@dp.message_handler(state=FormLogin.passwd)
async def process_passwds(message: types.Message, state: FSMContext):
	try:
		async with state.proxy() as data:
			data['passwd'] = message.text
			
			# Primeiro verifica as credenciais da IQ Option
			success, msg, _ = check_iq_credentials(data['email'], data['passwd'])
			if not success:
				await message.reply(f"❌ {msg}")
				await state.finish()
				return
				
			# Se as credenciais estão corretas, salva/atualiza no banco
			ok, userData = selectUserById(str(message.chat.id))
			if not ok:
				# Se o usuário não existe, vamos criar
				saveUser(str(message.chat.id), data['email'], data['passwd'], '2024-12-31')
				await message.reply("✅ Usuário cadastrado com sucesso!")
			else:
				# Se já existe, atualiza os dados
				saveUser(str(message.chat.id), data['email'], data['passwd'], userData['date_validade'])
				await message.reply("✅ Dados atualizados com sucesso!")
			await state.finish()
	except Exception as a:
		await state.finish()
		await message.reply("❌ ERRO: "+str(a))
		pass
#########################################LOGIN#############################################################
#############################################COFIG##########################################################
@dp.message_handler(commands='config')
async def cmd_config(message: types.Message):
		await FormConfig.stopwin.set()
		await message.reply("Digite o valor de Stop Win:")
@dp.message_handler(state=FormConfig.stopwin)
async def process_stopwin(message: types.Message, state: FSMContext):
		async with state.proxy() as data:
			data['stopwin'] = message.text
		await FormConfig.next()
		await message.reply("Digite o valor de Stop Loss:")
@dp.message_handler(state=FormConfig.stoploss)
async def process_stoploss(message: types.Message, state: FSMContext):
		async with state.proxy() as data:
			data['stoploss'] = message.text
		await FormConfig.next()
		await message.reply("Digite o valor de PayOut:")
@dp.message_handler(state=FormConfig.payout)
async def process_payout(message: types.Message, state: FSMContext):
		async with state.proxy() as data:
			data['payout'] = message.text
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
		for par in ACTIVESSC:
			markup.add(par)
		await FormConfig.next()
		await message.reply("Escolha o par de moeda ou digite(Verifique se está aberta):", reply_markup=markup)
@dp.message_handler(state=FormConfig.pair)
async def process_pair(message: types.Message, state: FSMContext):
		async with state.proxy() as data:
			data['pair'] = message.text
		await FormConfig.next()
		await message.reply("Digite o fator Gale:")
@dp.message_handler(state=FormConfig.factor_gale)
async def process_factor_gale(message: types.Message, state: FSMContext):
		async with state.proxy() as data:
			data['factor_gale'] = message.text
		await FormConfig.next()
		await message.reply("Digite a quantidade Gale:")
@dp.message_handler(state=FormConfig.amount_gale)
async def process_amount_gale(message: types.Message, state: FSMContext):
		async with state.proxy() as data:
			data['amount_gale'] = message.text
		await FormConfig.next()
		await message.reply("Digite o valor do investimento:")
@dp.message_handler(state=FormConfig.value_investment)
async def process_value_investment(message: types.Message, state: FSMContext):
		async with state.proxy() as data:
			data['value_investment'] = message.text
			userId = str(message.chat.id)
			stopwin = data['stopwin']
			stoploss = data['stoploss']
			payout = data['payout']
			pair = data['pair']
			factor_gale = data['factor_gale']
			amount_gale = data['amount_gale']
			value_investment = data['value_investment']
			saveConfigUser(userId, stopwin, stoploss, payout, pair, factor_gale, amount_gale, value_investment)
			await message.reply("Configuração salva com sucesso!")
			await state.finish()
	
#########################################CONFIG##############################################################
#################################RESUME#######################################################################
@dp.message_handler(commands='myconf')    
async def cmd_resume(message: types.Message):
		try:
			isOk, userData = selectConfigById(str(message.chat.id))
			if isOk:
				stopwin = userData.get("stopwin", "0")
				stoploss = userData.get("stoploss", "0")
				payout = userData.get("payout", "0")
				pair = userData.get("pair", "EURUSD")
				factor_gale = userData.get("factor_gale", "2")
				amount_gale = userData.get("amount_gale", "2")
				value_investment = userData.get("value_investment", "2")
				text = (
					f"Stop Win: {stopwin}\n"
					f"Stop Loss: {stoploss}\n"
					f"Investimento: {value_investment}\n"
					f"PayOut: {payout}\n"
					f"Paridade: {pair}\n"
					f"Fator Gale: {factor_gale}\n"
					f"Gale: {amount_gale}"
				)
				await message.reply(text)
			else:
				await message.reply("Configuração não encontrada para o usuário.")
		except Exception as e:
			await message.reply(f"Erro ao obter a configuração: {str(e)}")
###########################REUME#######################################################3
	
###############PAUSE##################
@dp.message_handler(commands='stop')
async def command_stop(message: types.Message):
		# Finaliza o processo associado ao usuário, se estiver em execução
		response = stop_process(message.chat.id)
		if response:
			await message.reply("Finalizado", reply_markup=mainMenu)
		else:
			await message.reply("Já foi finalizado", reply_markup=mainMenu)
################################
##############################PLAY###################################################################
@dp.message_handler(commands='play')
async def cmd_start(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("REAL", "TORNEIO", "PRATICA", "CANCELAR")
    await FormGo.cod.set()
    await message.reply("Onde vou atuar, no campo de batalha ou na arena de treinamento?", reply_markup=markup)

@dp.message_handler(state=FormGo.cod)
async def process_cods(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['cod'] = message.text
            
        if data['cod'].lower() == 'cancelar':
            await message.reply("Cancelado ", reply_markup=mainMenu)
            await state.finish()
            return
            
        # Verifica se o usuário existe e tem configurações
        ok, user_data = selectUserById(str(message.chat.id))
        if not ok or not user_data:
            await message.reply("❌ Você precisa fazer login primeiro usando o comando /login", reply_markup=mainMenu)
            await state.finish()
            return
            
        ok, config = selectConfigById(str(message.chat.id))
        if not ok or not config:
            await message.reply("❌ Configure suas operações primeiro usando o comando /config", reply_markup=mainMenu)
            await state.finish()
            return
            
        if data['cod'] not in ["PRATICA", "TORNEIO", "REAL"]:
            await message.reply("🤖: Opção inválida - use /config", reply_markup=mainMenu)
            await state.finish()
            return
            
        # Inicia o processo de operações
        try:
            start_process(message.chat.id, data['cod'])
            await message.reply(f"✅ Iniciando operações no modo {data['cod']}", reply_markup=mainMenu)
        except Exception as e:
            await message.reply(f"❌ Erro ao iniciar operações: {str(e)}", reply_markup=mainMenu)
            
        await state.finish()
        
    except Exception as e:
        await message.reply(f"❌ Erro inesperado: {str(e)}", reply_markup=mainMenu)
        await state.finish()

################################################PLAY################################################
#########################################ADM######################################################
@dp.message_handler(commands='promove')
async def cmd_promove(message: types.Message):
	if str(message.chat.id) == os.environ.get('ID_ADMIN'):
		await FormUpdateC.email.set()
		await message.reply("Qual ID da conta?")
	else:
		await message.reply("Você não tem permissão para executar esse comando.")
@dp.message_handler(state=FormUpdateC.email)
async def process_email(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		data['email'] = message.text
	await FormUpdateC.next()
	await message.reply("Isso aí {0}, agora preciso da quantidade de dias que esse usuario tem permisão ou envie cancelar para deesistir a operação".format(message.chat.first_name))
		
@dp.message_handler(state=FormUpdateC.date)
async def process_date(message: types.Message, state: FSMContext):
	try:
		async with state.proxy() as data:
			if 'canc' in message.text.lower():
				await state.finish()
			iduser = data['email']
			data_validade = (datetime.now(pytz.timezone('America/Sao_Paulo')) + timedelta(days=int(message.text))).strftime('%Y-%m-%d')  # Definimos a validade para 80 anos a partir de hoje em São Paulo
			
			ok, userData = selectUserById(str(iduser))
			if ok:
				saveUser(iduser,userData['email'], userData['password'], data_validade)		
				await message.reply("Dados alterados")
			else:		
				await message.reply("Não foi possivel buscar dados  desse id")
			await state.finish()
	except Exception as a:
		await state.finish()
		await message.reply("ERRO: "+str(a))
		pass

@dp.message_handler(commands='delete')
async def cmd_delete(message: types.Message):
	if str(message.chat.id) == os.environ.get('ID_ADMIN'):
		await FormDeleteC.email.set()
		await message.reply("Qual ID da conta?")
	else:
		await message.reply("Você não tem permissão para executar esse comando.")

@dp.message_handler(state=FormDeleteC.email)
async def process_emsinas(message: types.Message, state: FSMContext):
	try:
		async with state.proxy() as data:
			data['email'] = message.text
			if 'canc' in message.text.lower():
				await state.finish()
			iduser = message.text
				
			ok, userData = selectUserById(str(iduser))
			if ok:
				saveUser(iduser,userData['email'], userData['password'], '2000-07-06')		
				await message.reply("Dados alterados")
			else:		
				await message.reply("Não foi possivel buscar dados  desse id")
			await state.finish()
	except Exception as a:
		await state.finish()
		await message.reply("ERRO: "+str(a))
		pass
#######################################################ADM##############################################################################

@dp.message_handler(commands=['testar'])
async def cmd_test(message: types.Message):
    try:
        ok, userData = selectUserById(str(message.chat.id))
        if not ok:
            await message.reply("❌ Você precisa fazer login primeiro usando o comando /login")
            return
            
        await message.reply("🔄 Iniciando teste de operação na conta demo...")
        
        # Faz login e muda para conta demo
        success, msg, trader = check_iq_credentials(userData['email'], userData['password'], use_demo=True)
        if not success:
            await message.reply(f"❌ {msg}")
            return
            
        # Testa uma operação
        success, msg = test_binary_operation(trader)
        await message.reply(msg)
            
    except Exception as e:
        await message.reply(f"❌ Erro ao testar operação: {str(e)}")

@dp.message_handler()
async def bot_message(message: types.Message):
		# await bot.send_message(message.from_user.id, message.text) 
		if message.text == '👤':
			await cmd_login(message)
		elif message.text == '📑':
			await cmd_resume(message) 
		elif message.text == '⚙️':
			await cmd_config(message)	
		elif message.text == '▶️':
			await cmd_start(message)
		elif message.text == '⏸':
			await command_stop(message)
		else:
			await message.reply('Oi, Redirecione para menu com /start')
if __name__ == '__main__':
	try:
		dp.middleware.setup(MyMiddleware())
		start_polling(dp, skip_updates=True)
	except Exception as a:
		pass
