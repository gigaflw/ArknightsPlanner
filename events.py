from dataclasses import dataclass

class Events:
    _registry = {}

    def __init_subclass__(subcls, name=None):
        name = name or subcls.__name__
        if not hasattr(subcls, 'enabled'):
            subcls.enabled = True
        Events._registry[name] = subcls

    @classmethod
    def get_items(cls):
        return {
            name: event.items
            for name, event in cls._registry.items()
        }

    @classmethod
    def get_tradepaths(cls):
        def get_path(event):
            paths = event.tradepaths
            for path in paths:
                if isinstance(path[0], (int, float)):
                    path[0] = {event.items: path[0]}
            return paths

        return {
            name: get_path(event)
            for name, event in cls._registry.items()
            if event.enabled
        }

class 骑兵与猎人(Events):
    enabled = False

    items = '骑士金币'
    tradepaths = [
        # cost, items, stock
        [10, {'初级作战记录': 2}, 120],
        [25, {'中级作战记录': 2}, 50],
        [50, {'高级作战记录': 2}, 25],
        [80, {'1k龙门币': 50}, 100],
        [25, {'技巧概要·卷2': 1}, 50],
        [50, {'技巧概要·卷3': 1}, 25],
        [100, {'先锋芯片': 1}, 4],
        [25, {'固源岩': 1}, 40],
        [35, {'聚酸酯': 1}, 25],
        [60, {'装置': 1}, 15],
        [120, {'酮凝集组': 1}, 15],
        [120, {'异铁组': 1}, 15],
        [350, {'提纯源岩': 1}, 10],
        [500, {'糖聚块': 1}, 10],
        [500, {'RMA70-24': 1}, 10],
        [1200, {'聚合剂': 1}, 5],
        [1500, {'寻访凭证': 1}, 3],
    ]
