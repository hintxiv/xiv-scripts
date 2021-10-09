import pymem
import pymem.process
import time

ANIM_LOCK = 0x1D3CE68
BASE_LOCK = 0.5
NEW_LOCK = 0.5

pm = pymem.Pymem("ffxiv_dx11.exe")
client = pymem.process.module_from_name(pm.process_handle, "ffxiv_dx11.exe").lpBaseOfDll

last = 0
lock_start = 0

# Barebones "animation lock reducer"
while True:
    lock = pm.read_float(client + ANIM_LOCK)
    
    if (lock != 0):
        print(lock)

    # New lock encountered
    if lock > last and lock < 1.5:
        if lock > BASE_LOCK:
            pm.write_float(client + ANIM_LOCK, float( NEW_LOCK ))

        else:
            lock_start = time.time()

    last = lock
