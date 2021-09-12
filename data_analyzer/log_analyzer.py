from pathlib import Path
from .log_tools import *

LOG_PATH = 'data_analyzer/logs/09_08'

log_dir = Path(LOG_PATH)

vids_w_log = []
for l in log_dir.iterdir():
    if l.suffix == '.log':
        vids_w_log.append(l.stem)

for n in vids_w_log:
    logs = []
    with open(str((log_dir/vids_w_log).with_suffix('.log')),'r') as log:
        logs.append(line_to_dict(log.readline()))
    