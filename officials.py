import copy
from dataclasses import dataclass

def _acc(arr):
    ret = [0, 0] # 0/1 级时拥有经验 = 0；2 级时拥有经验 = arr[0]
    for val in arr:
        ret.append(ret[-1] + val)
    return ret

@dataclass
class Official:
    elite_level: int = 0
    level: int = 1
    skill_levels: int = (1, 1, 1)

    name = ''
    eng_name = ''
    stars = 0
    n_skills = 1
    elite_1_items = {}
    elite_2_items = {}
    skill_levelup_items = {}

    _registry = {}

    EXP_REQUIRED = [
        _acc([ # 精0: 1 ～ 50 级
            100, 117, 134, 151, 168, 185, 202, 219, 236, 253,
            270, 287, 304, 321, 338, 355, 372, 389, 406, 423,
            440, 457, 474, 491, 508, 525, 542, 559, 574, 589,
            605, 621, 637, 653, 669, 685, 701, 716, 724, 739,
            749, 759, 770, 783, 804, 820, 836, 852, 888,
        ]), _acc([ # 精1: 1 ～ 80 级
            120,   172,   224,   276,   328,   380,   432,   484,   536,   588,
            640,   692,   744,   796,   848,   900,   952,   1004,  1056,  1108,
            1160,  1212,  1264,  1316,  1368,  1420,  1472,  1524,  1576,  1628,
            1706,  1784,  1862,  1940,  2018,  2096,  2174,  2252,  2330,  2408,
            2584,  2760,  2936,  3112,  3288,  3464,  3640,  3816,  3992,  4168,
            4344,  4520,  4696,  4890,  5326,  6019,  6312,  6505,  6838,  7391,
            7657,  7823,  8089,  8355,  8621,  8887,  9153,  9419,  9605,  9951,
            10448, 10945, 11442, 11939, 12436, 12933, 13430, 13927, 14549,
        ]), _acc([ # 精2: 1 ～ 90 级
            191,   303,   415,   527,   639,   751,   863,   975,   1087,  1199,
            1311,  1423,  1535,  1647,  1759,  1871,  1983,  2095,  2207,  2319,
            2431,  2543,  2655,  2767,  2879,  2991,  3103,  3215,  3327,  3439,
            3602,  3765,  3928,  4091,  4254,  4417,  4580,  4743,  4906,  5069,
            5232,  5395,  5558,  5721,  5884,  6047,  6210,  6373,  6536,  6699,
            6902,  7105,  7308,  7511,  7714,  7917,  8120,  8323,  8526,  8729,
            9163,  9597,  10031, 10465, 10899, 11333, 11767, 12201, 12729, 13069,
            13747, 14425, 15103, 15781, 16459, 17137, 17815, 18493, 19171, 19849,
            21105, 22361, 23617, 24873, 26129, 27385, 28641, 29897, 31143,
        ])
    ]

    MONEY_REQUIRED = [
        _acc([ # 精0: 1 ～ 50 级
            30, 36, 43, 50, 57, 65, 73, 81, 90, 99,
            108, 118, 128, 138, 149, 160, 182, 206, 231, 258,
            286, 315, 346, 378, 411, 446, 482, 520, 557, 595,
            635, 677, 720, 764, 809, 856, 904, 952, 992, 1042,
            1086, 1131, 1178, 1229, 1294, 1353, 1413, 1474, 1572,
        ]), _acc([ # 精1: 1 ～ 80 级
            48,    71,    95,    120,   146,   173,   201,   231,   262,   293,
            326,   361,   396,   432,   470,   508,   548,   589,   631,   675,
            719,   765,   811,   859,   908,   958,   1010,  1062,  1116,  1171,
            1245,  1322,  1400,  1480,  1562,  1645,  1731,  1817,  1906,  1996,
            2171,  2349,  2531,  2717,  2907,  3100,  3298,  3499,  3705,  3914,
            4127,  4344,  4565,  4807,  5294,  6049,  6413,  6681,  7098,  7753,
            8116,  8378,  8752,  9132,  9518,  9909,  10306, 10709, 11027, 11533,
            12224, 12926, 13639, 14363, 15097, 15843, 16599, 17367, 18303,
        ]), _acc([ # 精2: 1 ～ 90 级
            76,    124,   173,   225,   279,   334,   392,   451,   513,   577,
            642,   710,   780,   851,   925,   1001,  1079,  1159,  1240,  1324,
            1410,  1498,  1588,  1680,  1773,  1869,  1967,  2067,  2169,  2273,
            2413,  2556,  2702,  2851,  3003,  3158,  3316,  3477,  3640,  3807,
            3976,  4149,  4324,  4502,  4684,  4868,  5055,  5245,  5438,  5634,
            5867,  6103,  6343,  6587,  6835,  7086,  7340,  7599,  7861,  8127,
            8613,  9108,  9610,  10120, 10637, 11163, 11696, 12238, 12882, 13343,
            14159, 14988, 15828, 16681, 17545, 18422, 19311, 20213, 21126, 22092,
            23722, 25380, 27065, 28778, 30519, 32287, 34083, 35906, 37745
        ])
    ]

    @staticmethod
    def get_level_cap(elite_level, stars):
        return {
            0: {1: 30, 2: 30, 3: 40, 4: 45, 5: 50, 6: 50},
            1: {3: 55, 4: 60, 5: 70, 6: 80},
            2: {4: 70, 5: 80, 6: 90}
        }[elite_level][stars]

    @classmethod
    def get_elite_1_item(cls):
        return cls.elite_1_items

    @classmethod
    def get_elite_2_item(cls):
        return cls.elite_2_items

    @classmethod
    def get_skill_levelup_item(cls, skill_level, skill_ind=1):
        return cls.skill_levelup_items[skill_ind-1][skill_level-1]

    @classmethod
    def get_official_by_name(cls, name):
        for realname, nicknames in {
            '阿米娅': ['阿米驴'],
            '伊芙利特': ['小火龙'],
            '艾雅法拉': ['羊', '小羊'],
            '能天使': ['阿能'],
            '杰西卡': ['流泪猫猫头', '富婆'],
            '推进之王': ['推王', '王维娜', '王大锤'],
            '德克萨斯': ['德狗', '德狗子'],
            '斯卡蒂': ['cba', 'CBA', '虎鲸'],
            '银灰': ['银老板'],
            '艾丝黛尔': ['鳄鱼妹'],
            '玫兰莎': ['玫剑圣'],
            '芙兰卡': ['芙剑圣'],
            '蛇屠箱': ['蛇皮箱', '色图箱'],
            '白面鸮': ['白咕咕'],
            '赫默': ['咕咕', '猫头鹰'],
            '安洁莉娜': ['洁哥'],
            '食铁兽': ['大熊猫'],
        }.items():
            if name in nicknames:
                name = realname
                break

        if name in Official._registry:
            return Official._registry[name]

        raise NameError(f"Official {repr(name)} undefined")

    def get_cur_level_exp(self):
        lv_map = self.EXP_REQUIRED
        cur_lv = self.level

        ret = 0

        for elv in 0, 1, 2:
            if elv < self.elite_level:
                lv_cap = self.get_level_cap(elite_level=elv, stars=self.stars)
                ret += lv_map[elv][lv_cap]
            elif elv == self.elite_level:
                ret += lv_map[elv][self.level]
        return ret

    def get_cur_level_money(self):
        lv_map = self.MONEY_REQUIRED
        cur_lv = self.level

        ret = 0

        for elv in 0, 1, 2:
            if elv < self.elite_level:
                lv_cap = self.get_level_cap(elite_level=elv, stars=self.stars)
                ret += lv_map[elv][lv_cap]
            elif elv == self.elite_level:
                ret += lv_map[elv][self.level]
        return ret

    def __init_subclass__(subcls, name=None):
        subcls.name = name or subcls.__name__
        Official._registry[subcls.name] = subcls

    def copy(self):
        return copy.copy(self)

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if k not in self.__dict__:
                raise ValueError(f"Can not set {k} to {v}")
            self.__dict__[k] = v


class official_upgrade_items_calculator:
    def __init__(self, official_cls):
        self.official = official_cls
        self.beg = official_cls()
        self.end = official_cls()

    def since(self, elite_level, level, skill_level):
        if isinstance(skill_level, int):
            skill_level = [skill_level] * self.official.n_skills
        self.beg.update(elite_level=elite_level, level=level, skill_levels=skill_level)
        return self

    def to(self, elite_level, level, skill_level):
        if isinstance(skill_level, int):
            skill_level = [skill_level] * self.official.n_skills
        self.end.update(elite_level=elite_level, level=level, skill_levels=skill_level)
        return self._calculate()

    def _calculate(self):
        result = {'龙门币': 0, '经验值': 0}
        def update_result(data_dict):
            for k, v in data_dict.items():
                if k in result:
                    result[k] += v
                else:
                    result[k] = v

        # elite_level
        vbeg, vend = [getattr(off, 'elite_level') for off in (self.beg, self.end)]
        if vbeg < 1 <= vend:
            update_result(self.beg.get_elite_1_item())
        if vbeg < 2 <= vend:
            update_result(self.beg.get_elite_2_item())

        # level
        cap = lambda val: 0 if val < 0 else val

        update_result({
           '龙门币': cap(self.end.get_cur_level_money() - self.beg.get_cur_level_money()),
           '经验值': cap(self.end.get_cur_level_exp() - self.beg.get_cur_level_exp()),
        })

        # skill level
        vbeg, vend = [getattr(off, 'skill_levels') for off in (self.beg, self.end)]
        gsli = self.official.get_skill_levelup_item

        if max(vbeg) <= 7:
            if max(vend) <= 7:
                for lv in range(vbeg[0], vend[0]):
                    update_result(gsli(skill_level=lv))
            else:
                for lv in range(vbeg[0], 7):
                    update_result(gsli(skill_level=lv))

                for ind, ve in enumerate(vend):
                    for lv in range(7, ve):
                        update_result(gsli(skill_level=lv, skill_ind=ind+1))
        else:
            for ind, (vb, ve) in enumerate(zip(vbeg, vend)):
                for lv in range(vb, ve):
                    update_result(gsli(skill_level=lv, skill_ind=ind+1))

        # covert unit
        result['1k龙门币'] = result.pop('龙门币') / 1000
        result['1k经验值'] = result.pop('经验值') / 1000

        return result

class Officials:
    @staticmethod
    def get_required_items_for(official_name):
        official = Official.get_official_by_name(official_name)
        return official_upgrade_items_calculator(official)

    @staticmethod
    def get_official(official_name):
        return Official.get_official_by_name(official_name)

##########################
# Demo officials
##########################
class Demo初雪(Official):
    stars = 5
    n_skills = 2

    @classmethod
    def get_elite_1_item(cls):
        return {'龙门币': 2e4, '辅助芯片': 4, '糖': 4, '异铁': 3}

    @classmethod
    def get_elite_2_item(cls):
        return {'龙门币': 12e4, '辅助双芯片': 3, '酮阵列': 7, '研磨石': 11}

    @classmethod
    def get_skill_levelup_item(cls, skill_level, skill_ind=1):
        if skill_level < 1 or skill_level > 9:
            raise ValueError(f"Invalid skill_level: {skill_level} ")

        if skill_ind < 1 or skill_ind > cls.n_skills:
            raise ValueError(f"Invalid skill_ind: {skill_ind} ")

        skill_level -= 1 # 1-base -> 0-base
        skill_ind -= 1 # 1-base -> 0-base

        if skill_level < 6: # 0 ~ 5
            return [
                {'技巧概要·卷1': 4},
                {'技巧概要·卷1': 4, '代糖': 7},
                {'技巧概要·卷2': 6, '聚酸酯': 3},
                {'技巧概要·卷2': 6, '异铁': 4},
                {'技巧概要·卷2': 6, '研磨石': 3},
                {'技巧概要·卷3': 6, 'RMA70-12': 2, '聚酸酯组': 3},
            ][skill_level]
        elif skill_level < 9: # 6 ~ 8
            return [
                [
                    {'技巧概要·卷3': 5, '提纯源岩': 3, '研磨石': 4},
                    {'技巧概要·卷3': 6, '聚酸酯块': 3, '提纯源岩': 6},
                    {'技巧概要·卷3': 10, '聚合剂': 4, '改量装置': 3},
                ], [
                    {'技巧概要·卷3': 5, '糖聚块': 3, 'RMA70-12': 3},
                    {'技巧概要·卷3': 6, '异铁块': 3, '糖聚块': 5},
                    {'技巧概要·卷3': 10, '双极纳米片': 4, '异铁块': 3},
                ],
            ][skill_ind][skill_level-6]


import json
import os
import re
from util import ROOT

def register_official(data):
    skill_names = []
    for skill_levelup_title in data['技能升级']:
        if re.match(r'(.*) [0-9]+→[0-9]+', skill_levelup_title):
            skill_name = skill_levelup_title.split()[0]
            if skill_name not in skill_names:
                skill_names.append(skill_name)

    _skill_levelup_items = []

    for skill_name in skill_names:
        _skill_levelup_items.append([])

        for skill_level in range(9):
            if skill_level < 6:
                items = data['技能升级'].get(f'{skill_level+1}→{skill_level+2}')
                if not items:
                    break
            else:
                items = data['技能升级'].get(f'{skill_name} {skill_level+1}→{skill_level+2}')
                if not items:
                        break

            items = {k: int(v.strip(',')) for k, v in items.items()}
            _skill_levelup_items[-1].append(items)

    class new_official(Official, name=data['name']):
        name = data['name']
        eng_name = data['eng_name']
        stars = int(data['星级'])
        elite_1_items = data['精英化'].get('1', {})
        elite_2_items = data['精英化'].get('2', {})
        n_skills = len(skill_names)
        skill_levelup_items = _skill_levelup_items

    return new_official

def register_officials():
    # CRAWLER_PATH = os.path.join(ROOT, "crawlers/results/officials.jl")
    CRAWLER_PATH = "crawlers/results/officials.jl"

    with open(CRAWLER_PATH, "r") as f:
        for line in f:
            data = json.loads(line)
            register_official(data)

register_officials()

if __name__ == '__main__':
    print(Officials.get_required_items_for('初雪').since(
        elite_level=0, level=1, skill_level=1
    ).to(
        elite_level=2, level=1, skill_level=7
    ))
    print(Officials.get_required_items_for('Demo初雪').since(
        elite_level=0, level=1, skill_level=1
    ).to(
        elite_level=2, level=1, skill_level=7
    ))
