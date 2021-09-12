from pathlib import Path
from log_tools import *
import numpy as np

LOG_PATH = 'data_analyzer/logs/09_10'

log_dir = Path(LOG_PATH)

vids_w_log = []
for l in log_dir.iterdir():
    if l.suffix == '.log':
        vids_w_log.append(l.stem)

room_buttons = np.zeros(4, dtype=int)

for n in vids_w_log:
    logs = []
    with open(str((log_dir/n).with_suffix('.log')),'r') as log:
        lines = log.readlines()
        for line in lines:
            logs.append(line_to_dict(line))

    
    for l in logs:
        if l['type'] == 'button_pressed':
            room, _ = l['data'].split('/')
            room = int(room)
            room_buttons[room] += 1

print(room_buttons)