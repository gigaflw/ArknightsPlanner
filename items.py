import json

from typing import Dict
from dataclasses import dataclass

from events import Events

JOBS = '先锋 近卫 重装 狙击 辅助 术师 医疗 特种'.split()

_ITEMS = {
    '基础': '1d 至纯源石 理智 信用 1k龙门币 1k经验值',
    '抽卡': '合成玉 寻访凭证 招聘许可 加急许可',

    '凭证': '资质凭证 高级凭证 采购凭证',
    '作战记录': '基础作战记录 初级作战记录 中级作战记录 高级作战记录',

    'T1': '源岩 代糖 酯原料 异铁碎片 双酮 破损装置',
    'T2': '固源岩 糖 聚酸酯 异铁 酮凝集 装置',
    'T3': '固源岩组 糖组 聚酸酯组 异铁组 酮凝集组 全新装置 扭转醇 轻锰矿 研磨石 RMA70-12',
    'T4': '提纯源岩 糖聚块 聚酸酯块 异铁块 酮阵列 改量装置 白马醇 三水锰矿 五水研磨石 RMA70-24',
    'T5': '聚合剂 双极纳米片 D32钢',

    '芯片': [f'{cate}{chip}' for cate in JOBS for chip in ('芯片', '双芯片', '芯片组')],
    '突破': '芯片助剂 信物复制品 信物原件 信物藏品 传承信物 遗产信物 皇家信物',

    '技能': '技巧概要·卷1 技巧概要·卷2 技巧概要·卷3',

    '基建': '赤金 无人机 碳 碳素 碳素组 基础加固建材 进阶加固建材 高级加固建材 家具零件',

    **{
        f"活动<{name}>": items
        for name, items in Events.get_items().items()
    },
}

class _ItemCollection:
    def __init__(self):
        self.name_to_id = {}
        self.items = []
        self.name_to_category = {}

        for category, items in _ITEMS.items():
            if isinstance(items, str):
                items = items.split()
            for item in items:
                assert item not in self.items

                self.name_to_id[item] = len(self.items)
                self.items.append(item)
                self.name_to_category[item] = category

    def __iter__(self):
        return self.items.__iter__()

    def __len__(self):
        return len(self.items)

    def __contains__(self, item):
        return item in self.items

    def to_id(self, name):
        return self.name_to_id[name]

    def to_name(self, id):
        return self.items[id]

    def validate(self, item_names):
        for name in item_names:
            if name not in self:
                raise NameError(f"Unknown item: {name}")

ALL_ITEMS = _ItemCollection()


@dataclass
class TradePath:
    src: Dict[str, float]
    dst: Dict[str, float]
    tag: str

    max_cnt: int = None
    max_cnt_per_day: int = None

    def __post_init__(self):
        for collection in self.src, self.dst:
            for item in collection:
                if item not in ALL_ITEMS:
                    raise ValueError(item)

    def __bool__(self):
        return bool(self.src) and bool(self.dst)

    def __repr__(self):
        def float_dict_str(d):
            return '{' + ', '.join(f"{repr(k)}:{v:.2f}" for k, v in d.items()) + '}'

        return f"TradePath(tag={repr(self.tag)}, dst={float_dict_str(self.dst)}, src={float_dict_str(self.src)},)"

class _TradePathCollection(list):
    @staticmethod
    def get_tradepaths_from_drops():
        CRAWLER_PATH = "crawlers/results/droprates.jl"

        paths = []
        with open(CRAWLER_PATH, "r") as f:
            for line in f:
                data = json.loads(line)

                drops = {
                    item['item']['name']: int(item['quantity']) / int(item['times'])
                    for item in data["drops"]
                    if item['item']['name'] != '家具'
                }
                ap_cost = int(data["stage"]["apCost"])

                if data["stage"]["code"].startswith('GT'):
                    drops['骑士金币'] = ap_cost * 10
                drops['1k龙门币'] = ap_cost * 10 * 1.2 / 1000

                path = TradePath(
                    src={"理智": ap_cost},
                    dst=drops,
                    tag=data["stage"]["code"]
                )

                paths.append(path)

        return paths

TRADE_PATHS = _TradePathCollection([
    TradePath({'1d': 1}, {'理智': 240, '1k龙门币': 45,'中级作战记录': 20}, "自然恢复 1 天"),
    TradePath({'赤金': 1}, {'1k龙门币': 0.5}, "贸易站"),

    # 作战记录
    TradePath({'高级作战记录': 1}, {'1k经验值': 2}, "喂经验"),
    TradePath({'中级作战记录': 1}, {'1k经验值': 1}, "喂经验"),
    TradePath({'初级作战记录': 1}, {'1k经验值': .2}, "喂经验"),
    TradePath({'基础作战记录': 1}, {'1k经验值': .1}, "喂经验"),

    # 资质凭证
    *[
        TradePath({'资质凭证': n}, items, "资质凭证第一层", max_cnt_per_day=max_n/30)
        for n, items, max_n in [
            (240, {'寻访凭证': 1}, 2),
            (40, {'合成玉': 100}, 6),
            (10, {'1k龙门币': 4}, 15),
            (40, {'家具零件': 100}, 5),
            (8, {'招聘许可': 1}, 15),
            (10, {'中级作战记录': 4}, 15),
            (10, {'赤金': 8}, 15),
        ]
    ],

    *[
        TradePath({'资质凭证': n}, items, "资质凭证第二层", max_cnt_per_day=max_n/30)
        for n, items, max_n in [
            (450, {'寻访凭证': 1}, 2),
            (15, {'招聘许可': 1}, 20),
            (25, {'固源岩组': 1}, 15),
            (30, {'糖组': 1}, 15),
            (30, {'聚酸酯组': 1}, 15),
            (35, {'异铁组': 1}, 15),
            (35, {'酮凝集组': 1}, 15),
            (45, {'全新装置': 1}, 15),
            (30, {'扭转醇': 1}, 15),
            (35, {'轻锰矿': 1}, 15),
            (40, {'研磨石': 1}, 15),
            (45, {'RMA70-12': 1}, 15),
        ]
    ],

    TradePath({'资质凭证': 100}, {'1k龙门币': 10}, "资质凭证第三层", max_cnt_per_day=15/30),
    TradePath({'资质凭证': 50}, {'合成玉': 30}, "资质凭证第三层"),

    # 高级凭证
    TradePath({'高级凭证': 10}, {'寻访凭证': 10}, "高级凭证"),
    TradePath({'高级凭证': 5}, {'加急许可': 1}, "高级凭证"),
    TradePath({'高级凭证': 35}, {'遗产信物': 1}, "高级凭证"),
    TradePath({'高级凭证': 135}, {'皇家信物': 1}, "高级凭证"),
    TradePath({'高级凭证': 10}, {'提纯源岩': 1}, "高级凭证"),
    TradePath({'高级凭证': 10}, {'糖聚块': 1}, "高级凭证"),
    TradePath({'高级凭证': 15}, {'酮阵列': 1}, "高级凭证"),
    TradePath({'高级凭证': 20}, {'改量装置': 1}, "高级凭证"),
    TradePath({'高级凭证': 10}, {'白马醇': 1}, "高级凭证"),
    TradePath({'高级凭证': 10}, {'三水锰矿': 1}, "高级凭证"),
    TradePath({'高级凭证': 15}, {'芯片助剂': 1}, "高级凭证", max_cnt_per_day=30/15),

    # 采购凭证
    TradePath({'采购凭证': 90}, {'芯片助剂': 1}, "采购凭证"),
    TradePath({'采购凭证': 45}, {'传承信物': 1}, "采购凭证"),
    TradePath({'采购凭证': 180}, {'遗产信物': 1}, "采购凭证"),
    TradePath({'采购凭证': 720}, {'皇家信物': 1}, "采购凭证"),

    # 加工站: T5
    TradePath({'三水锰矿': 1, '五水研磨石': 1, 'RMA70-24': 1, '1k龙门币': 0.4}, {'D32钢': 1}, "加工站"),
    TradePath({'改量装置': 1, '白马醇': 2, '1k龙门币': 0.4}, {'双极纳米片': 1}, "加工站"),
    TradePath({'提纯源岩': 1, '异铁块': 1, '酮阵列': 1, '1k龙门币': 0.4}, {'聚合剂': 1}, "加工站"),

    # 加工站: T4
    TradePath({'RMA70-12': 1, '固源岩组': 2, '酮凝集组': 1, '1k龙门币': 0.3}, {'RMA70-24': 1}, "加工站"),
    TradePath({'研磨石': 1, '异铁组': 1, '全新装置': 1, '1k龙门币': 0.3}, {'五水研磨石': 1}, "加工站"),
    TradePath({'轻锰矿': 2, '聚酸酯组': 1, '扭转醇': 1, '1k龙门币': 0.3}, {'三水锰矿': 1}, "加工站"),
    TradePath({'扭转醇': 1, '糖组': 1, 'RMA70-12': 1, '1k龙门币': 0.3}, {'白马醇': 1}, "加工站"),

    # 加工站: T1 ~ T3
    TradePath({'破损装置': 3, '1k龙门币': 0.1}, {'装置': 1}, "加工站"),
    TradePath({'装置': 4, '1k龙门币': 0.2}, {'全新装置': 1}, "加工站"),
    TradePath({'全新装置': 1, '固源岩组': 2, '研磨石': 1, '1k龙门币': 0.3}, {'改量装置': 1}, "加工站"),

    TradePath({'双酮': 3, '1k龙门币': 0.1}, {'酮凝集': 1}, "加工站"),
    TradePath({'酮凝集': 4, '1k龙门币': 0.2}, {'酮凝集组': 1}, "加工站"),
    TradePath({'酮凝集组': 2, '糖组': 1, '轻锰矿': 1, '1k龙门币': 0.3}, {'酮阵列': 1}, "加工站"),

    TradePath({'异铁碎片': 3, '1k龙门币': 0.1}, {'异铁': 1}, "加工站"),
    TradePath({'异铁': 4, '1k龙门币': 0.2}, {'异铁组': 1}, "加工站"),
    TradePath({'异铁组': 2, '全新装置': 1, '聚酸酯组': 1, '1k龙门币': 0.3}, {'异铁块': 1}, "加工站"),

    TradePath({'酯原料': 3, '1k龙门币': 0.1}, {'聚酸酯': 1}, "加工站"),
    TradePath({'聚酸酯': 4, '1k龙门币': 0.2}, {'聚酸酯组': 1}, "加工站"),
    TradePath({'聚酸酯组': 2, '酮凝集组': 1, '扭转醇': 1, '1k龙门币': 0.3}, {'聚酸酯块': 1}, "加工站"),

    TradePath({'代糖': 3, '1k龙门币': 0.1}, {'糖': 1}, "加工站"),
    TradePath({'糖': 4, '1k龙门币': 0.2}, {'糖组': 1}, "加工站"),
    TradePath({'糖组': 2, '异铁组': 1, '轻锰矿': 1, '1k龙门币': 0.3}, {'糖聚块': 1}, "加工站"),

    TradePath({'源岩': 3, '1k龙门币': 0.1}, {'固源岩': 1}, "加工站"),
    TradePath({'固源岩': 5, '1k龙门币': 0.2}, {'固源岩组': 1}, "加工站"),
    TradePath({'固源岩组': 4, '1k龙门币': 0.3}, {'提纯源岩': 1}, "加工站"),

    # 加工站: 芯片
    *[
        TradePath({'芯片助剂': 1, f'{job}芯片组': 2}, {f'{job}双芯片': 1}, "加工站")
        for job in JOBS
    ],

    # 加工站: 建材
    TradePath({'碳': 2, '1k龙门币': .8}, {'基础加固建材': 1}, "加工站"),
    TradePath({'碳素': 2, '1k龙门币': 2.4}, {'进阶加固建材': 1}, "加工站"),
    TradePath({'碳素组': 2, '1k龙门币': 7.2}, {'高级加固建材': 1}, "加工站"),
    TradePath({'碳': 3}, {'碳素': 1}, "加工站"),
    TradePath({'碳素': 3}, {'碳素组': 1}, "加工站"),
    TradePath({'碳': 1}, {'家具零件': 4}, "加工站"),
    TradePath({'碳素': 1}, {'家具零件': 8}, "加工站"),
    TradePath({'碳素组': 1}, {'家具零件': 12}, "加工站"),
    TradePath({'基础加固建材': 1}, {'家具零件': 8}, "加工站"),
    TradePath({'进阶加固建材': 1}, {'家具零件': 16}, "加工站"),
    TradePath({'高级加固建材': 1}, {'家具零件': 24}, "加工站"),
    
    # 加工站: 技能书
    TradePath({'技巧概要·卷1': 3}, {'技巧概要·卷2': 1}, "加工站"),
    TradePath({'技巧概要·卷2': 3}, {'技巧概要·卷3': 1}, "加工站"),

    # 关卡掉落
    *_TradePathCollection.get_tradepaths_from_drops(),
    TradePath({'理智': 30}, {'技巧概要·卷3': 2.5, '技巧概要·卷2': 1.5, '技巧概要·卷1': 1.5}, "CA-5"),
    TradePath({'理智': 30}, {'高级作战记录': 3, '中级作战记录': 1, '初级作战记录': 1}, "LS-5"),
    TradePath({'理智': 30}, {'采购凭证': 21}, "AP-5"),
    TradePath({'理智': 30}, {'1k龙门币': 7.5}, "CE-5"),

    *[
        TradePath({'理智': 18}, {f'{job1}芯片': 0.5, f'{job2}芯片': 0.5,}, chapter)
        for job1, job2, chapter in [
            ('重装', '医疗', 'PR-A-1'),
            ('狙击', '术师', 'PR-B-1'),
            ('先锋', '辅助', 'PR-C-1'),
            ('近卫', '特种', 'PR-D-1'),
        ]
    ],
    *[
        TradePath({'理智': 36}, {f'{job1}芯片组': 0.5, f'{job2}芯片组': 0.5,}, chapter)
        for job1, job2, chapter in [
            ('重装', '医疗', 'PR-A-2'),
            ('狙击', '术师', 'PR-B-2'),
            ('先锋', '辅助', 'PR-C-2'),
            ('近卫', '特种', 'PR-D-2'),
        ]
    ],

    # 公开招募
    TradePath({'招聘许可': 1}, {'资质凭证': 5+5}, '公开招募'),

    # 日常 & 周常 & 签到
    TradePath({}, {
        '1k龙门币': 3.5,
        '技巧概要·卷1': 2,
        '招聘许可': 1,
        '基础作战记录': 8,
        '初级作战记录': 5,
        '采购凭证': 5,
        '合成玉': 100,
        }, '日常任务', max_cnt_per_day=1
    ),

    TradePath({}, {
        '1k龙门币': 13,
        '技巧概要·卷1': 5,
        '招聘许可': 9,
        '基础作战记录': 4,
        '初级作战记录': 0,
        '中级作战记录': 4,
        '高级作战记录': 4,
        '赤金': 14,
        '采购凭证': 30,
        '资质凭证': 20,
        '合成玉': 500,
        }, '周常任务', max_cnt_per_day=1/7
    ),

    TradePath({}, {
        '1k龙门币': 2 + 4 + 6 + 8 + 10,
        '技巧概要·卷1': 5 + 10,
        '技巧概要·卷2': 5,
        '技巧概要·卷3': 6,
        '基础作战记录': 10,
        '初级作战记录': 10,
        '中级作战记录': 10,
        '高级作战记录': 4 + 5,
        '赤金': 6 + 10 + 15,
        '采购凭证': 8 + 25,
        '资质凭证': 10,
        '高级凭证': 5,
        '招聘许可': 2 + 3,
        '寻访凭证': 1,
        '芯片助剂': 1,
        }, '每月签到', max_cnt_per_day=1/30
    ),
])

for event_name, paths in Events.get_tradepaths().items():
    TRADE_PATHS.extend([
        TradePath(cost, items, f"活动商店<{event_name}>", max_cnt=stock)
        for cost, items, stock in paths
    ])
