def line_to_dict(log_line:str):
    f, m, d, hh, mm, ss, name, data = log_line.split(',')
    return {
        'frame' : int(f),
        'month' : int(m),
        'day' : int(d),
        'hour' : int(hh),
        'minute' : int(mm),
        'second' : int(ss),
        'type' : name,
        'data' : data,
    }