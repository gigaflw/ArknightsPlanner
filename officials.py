import copy
from dataclasses import dataclass

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

    EXP_REQUIRED = {
        0: {
            1: 0,
            10: 1872, 15: 3875, 20: 6517,
            25: 9842, 30: 13800, 35: 18190,
            40: 23000, 45: 28800, 50: 38800
        },
        1: {
            1: 0,
            10: 3672, 15: 8232, 20: 14592,
            25: 22752, 30: 32712, 35: 44472,
            40: 58032, 45: 73392, 50: 90552,
            55: 110000, 60: 141000, 65: 180315,
            70: 226000, 75: 280725, 80: 350000
        }
    }

    MONEY_REQUIRED = {
        0: {
            1: 0,
            10: 702, 15: 1532, 20: 2736,
            25: 4479, 30: 6611, 35: 9675,
            40: 14180, 45: 21109, 50: 32394
        },
        1: {
            1: 0,
            10: 1741, 15: 4152, 20: 7735,
            25: 12918, 30: 19790, 35: 28548,
            40: 39390, 45: 52337, 50: 67930,
            55: 86793, 60: 118128, 65: 160352,
            70: 211732, 75: 276508, 80: 362142
        }
    }

    @staticmethod
    def get_level_cap(elite_level, stars):
        return {
            0: {2: 30, 3: 40, 4: 45, 5: 50, 6: 50},
            1: {3: 55, 4: 60, 5: 70, 6: 80}
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

        if self.elite_level == 0:
            return lv_map[0][self.level]
        elif self.elite_level == 1:
            e0_exp = lv_map[0][self.get_level_cap(elite_level=0, stars=self.stars)]
            return e0_exp + lv_map[1][self.level]
        elif self.elite_level == 2:
            assert self.level == 1
            e0_exp = lv_map[0][self.get_level_cap(elite_level=0, stars=self.stars)]
            e1_exp = lv_map[1][self.get_level_cap(elite_level=1, stars=self.stars)]
            return e0_exp + e1_exp

    def get_cur_level_money(self):
        lv_map = self.MONEY_REQUIRED

        if self.elite_level == 0:
            return lv_map[0][self.level]
        elif self.elite_level == 1:
            e0_money = lv_map[0][self.get_level_cap(elite_level=0, stars=self.stars)]
            return e0_money + lv_map[1][self.level]
        elif self.elite_level == 2:
            assert self.level == 1
            e0_money = lv_map[0][self.get_level_cap(elite_level=0, stars=self.stars)]
            e1_money = lv_map[1][self.get_level_cap(elite_level=1, stars=self.stars)]
            return e0_money + e1_money

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
