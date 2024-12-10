from datetime import datetime

def controlMessage(message):
    try:
        msg = message.text.lower()
        if msg == '/start':
            return True
        elif msg == '/login':
            return True
        elif msg == '/config':
            return True
        elif msg == '/resume':
            return True
        elif msg == '/stop':
            return True
        elif msg == '/go':
            return True
        elif msg == '/promove':
            return True
        elif msg == '/delete':
            return True
        return False
    except:
        return False
