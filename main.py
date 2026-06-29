from collections import deque

from api import PanAPI
from conf.pa import cf
from ctx import ctx
from graph import Graph, Graph3D
from mon import monitor

def init():
    ctx['api'] = PanAPI(cf)
    ctx["history"] = deque(maxlen=cf['time_window'])
    # ctx["graph"] = Graph(ctx)
    ctx["graph"] = Graph3D(ctx)


if __name__ == '__main__':
    init()
    monitor()
