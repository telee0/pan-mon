
import time

from conf.pa import cf
from ctx import ctx

def monitor():
    api = ctx["api"]
    history = ctx["history"]

    while True:
        sample = api.show_run_res_mon()
        history.append(sample)
        ctx["graph"].update()
        time.sleep(cf["time_interval"])
