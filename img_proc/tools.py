import numpy as np
GRAVITY_C = 50

def gravity(rc, last_rc = None):
    if last_rc is None:
        last_rc = np.array([r,c])
    delta = np.subtract(rc, last_rc)
    dist = np.linalg.norm(delta)
    if dist > GRAVITY_C:
        new_delta = delta * (GRAVITY_C**2)/(dist**2)
        new_rc = (last_rc + new_delta).astype(np.int)
    else:
        new_rc = last_rc
    return new_rc
