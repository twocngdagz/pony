import sys, time, threading
from os.path import dirname
from itertools import count

def detect_mode():
    try: 
        mod_wsgi = sys.modules['mod_wsgi']
        return 'MOD_WSGI'
    except KeyError:
        try: sys.modules['__main__'].__file__
        except AttributeError:  return 'INTERACTIVE'
        return 'NATIVE'

RUNNED_AS = detect_mode()

MAIN_FILE = None
if RUNNED_AS == 'NATIVE':
    MAIN_FILE = sys.modules['__main__'].__file__
elif RUNNED_AS == 'MOD_WSGI':
    for module_name, module in sys.modules.items():
        if module_name.startswith('_mod_wsgi_'):
            MAIN_FILE = module.__file__
            break

MAIN_DIR = None
if MAIN_FILE is not None:
    MAIN_DIR = dirname(MAIN_FILE)

shutdown = False

shutdown_list = []

def on_shutdown(func):
    if func not in shutdown_list: shutdown_list.append(func)
    return func

def exitfunc():
    mainloop()
    _shutdown()
    prev_func()

if RUNNED_AS == 'INTERACTIVE': pass
elif hasattr(threading, '_shutdown'):
    prev_func = threading._shutdown
    threading._shutdown = exitfunc
else:
    prev_func = sys.exitfunc
    sys.exitfunc = exitfunc

mainloop_counter = count()

_do_mainloop = False

def mainloop():
    if not _do_mainloop or RUNNED_AS != 'NATIVE' or mainloop_counter.next(): return
    try:
        while True:
            if shutdown: break
            time.sleep(1)
    except:
        try: log_exc = logging.log_exc
        except NameError: pass
        else: log_exc()

shutdown_counter = count()

def _shutdown():
    if shutdown_counter.next(): return
    for func in reversed(shutdown_list): func()
