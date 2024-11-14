import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import subprocess
# import multiprocessing
import json
from queue import Queue, Empty
import threading
import os
from time import sleep
import psutil
import os


def enqueue_output(out, queue):
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()


def runserver():
    if fr2.get('0.0', 'end'):
        fr2.configure(state='normal')
        fr2.delete('0.0', 'end')
        fr2.configure(state='disabled')


    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = '1'


    global serverProcess
    serverProcess = subprocess.Popen(
        [
            config['pythonInterpreterPath'],
            config['manage.pyPath'],
            'runserver'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    q_stdout = Queue()
    q_stderr = Queue()
    t_stdout = threading.Thread(target=enqueue_output, args=(serverProcess.stdout, q_stdout))
    t_stderr = threading.Thread(target=enqueue_output, args=(serverProcess.stderr, q_stderr))
    t_stdout.daemon = True
    t_stderr.daemon = True
    t_stdout.start()
    t_stderr.start()


    while serverProcess:
        print('iteration')
        try:
            output = q_stdout.get_nowait()
        except Empty:
            output = None

        try:
            error = q_stderr.get_nowait()
        except Empty:
            error = None
        # output = process.stdout.readline()
        # error = process.stderr.readline()


        if output:
            fr2.configure(state='normal')
            fr2.insert('end', output.strip() + '\n')
            fr2.configure(state='disabled')
            print('\tgot an output')
        else:
            print('\tno output')
        if error:
            fr2.configure(state='normal')
            fr2.insert('end', error.strip() + '\n')
            fr2.configure(state='disabled')
            print('\terror')
        else:
            print('\tno error')
        if serverProcess and serverProcess.poll() is not None:
            cnv.itemconfig(circle, fill='red')
            print('\tbroke')
            break
        sleep(0.3)


def poweroffserver():
    global serverProcess
    cnv.itemconfig(circle, fill='green')
    state.configure(text='Server state: Powered off')
    fr2.configure(state='normal')
    fr2.insert('end', '-'*45 + '\nSERVER POWERED OFF\n' + '-'*45 + '\n')
    fr2.configure(state='disabled')
    # serverProcess.terminate()
    # serverProcess.wait()
    # os.system(f'taskkill /F /PID {serverProcess}')
    parent = psutil.Process(serverProcess.pid)
    for child in parent.children(recursive=True):
        child.terminate()
    parent.terminate()
    
    gone, still_alive = psutil.wait_procs(parent.children(recursive=True), timeout=5)
    for p in still_alive:
        p.kill()
    parent.wait()
    serverProcess = None


def on_press(ev):
    if (75**2 >= (ev.x - 75)**2 + (ev.y - 75)**2):
        global serverProcess
        if not serverProcess:
            cnv.itemconfig(circle, fill='red')
            state.configure(text='Server state: Running')
            threading.Thread(target=runserver, daemon=True).start()
        else:
            poweroffserver()


def switch_view(val):
    global current_frame
    if val == 'Run/Stop':
        current_frame.pack_forget()
        fr1.pack()
        current_frame = fr1
    elif val == 'Output':
        current_frame.pack_forget()
        fr2.pack(expand=True, padx=5, pady=5)
        current_frame = fr2
    elif val == 'Configuration':
        current_frame.pack_forget()
        fr3.pack()
        current_frame = fr3


def select_interpreter():
    path = filedialog.askopenfilename(filetypes=[('Executable', 'python.exe')])
    if path:
        if path == config['pythonInterpreterPath']:
            return
        config['pythonInterpreterPath'] = path
        with open('config.json', 'w') as file:
            file.write(json.dumps(config, indent=4))
        interpreter_path_lbl.configure(text=path)

def select_manage_py():
    path = filedialog.askopenfilename(filetypes=[('Manage file', 'manage.py')])
    if path:
        if path == config['manage.pyPath']:
            return
        config['manage.pyPath'] = path
        with open('config.json', 'w') as file:
            file.write(json.dumps(config, indent=4))
        managepy_path_lbl.configure(text=path)


def onclose():
    if serverProcess: 
        # os.system(f'taskkill /F /PID {serverProcess.pid}')
        poweroffserver()
    root.destroy()


with open('config.json', 'r') as file:
    config = json.loads(file.read())


serverProcess: subprocess.Popen = None
isServerRunning = False


root = ctk.CTk()
root.title('Django server switch')
root.geometry('400x300')
root.minsize(400, 300)
root.resizable(True, False)
root.protocol('WM_DELETE_WINDOW', onclose)


sw = ctk.CTkSegmentedButton(root, values=['Run/Stop', 'Output', 'Configuration'], command=switch_view)
sw.set('Run/Stop')
sw.pack()

fr1 = tk.Frame(bg='#242424')
fr1.pack()
fr2 = ctk.CTkTextbox(root, width=2000, height=2000)
fr2.configure(state='disabled')
fr3 = tk.Frame(bg='#242424', width=400)
current_frame = fr1


ctk.CTkLabel(fr1, text='Press button below to run the server').pack(pady=20)
cnv = tk.Canvas(fr1, bg='#242424', width=150, height=150, highlightthickness=0)
circle = cnv.create_oval(0, 0, 150, 150, fill='green')
cnv.pack(pady=30)
cnv.bind('<Button-1>', on_press)
state = ctk.CTkLabel(fr1, text='Server state: Powered off')
state.pack(pady=10)



ctk.CTkLabel(fr3, text='Python interpreter path:').pack(padx=20, anchor='w')
interpreter_path_lbl = ctk.CTkLabel(fr3, text=config['pythonInterpreterPath'])
interpreter_path_lbl.pack(padx=40, pady=15)
ctk.CTkButton(fr3, text='Select "python.exe"', command=select_interpreter).pack()
line = tk.Canvas(fr3, width=2000, height=5, bg='#242424', highlightthickness=0)
line.create_line(0, 3, 2000, 3, fill='#f0f0f0')
line.pack(pady=15)
ctk.CTkLabel(fr3, text='manage.py file path:').pack(padx=20, anchor='w')
managepy_path_lbl = ctk.CTkLabel(fr3, text=config['manage.pyPath'])
managepy_path_lbl.pack(padx=40, pady=15)
ctk.CTkButton(fr3, text='Select "manage.py"', command=select_manage_py).pack()
root.mainloop()