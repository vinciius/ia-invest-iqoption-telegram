from aiogram.dispatcher.filters.state import State, StatesGroup

class FormLogin(StatesGroup):
    email = State()
    passwd = State()

class FormConfig(StatesGroup):
    stopwin = State()
    stoploss = State()
    payout = State()
    pair = State()
    factor_gale = State()
    amount_gale = State()
    value_investment = State()

class FormGo(StatesGroup):
    cod = State()

class FormUpdateC(StatesGroup):
    email = State()
    date = State()

class FormDeleteC(StatesGroup):
    email = State()
