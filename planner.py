import os
import time
import sys
import re
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import scipy.optimize
import yaml

from items import ALL_ITEMS, TRADE_PATHS, TradePath
from officials import Officials
from util import ROOT

REPORT_PATH = os.path.join(ROOT, 'reports')

class Audit(dict):
    def __init__(self, items: dict, all_items: list):
        super().__init__(items)
        self._all_items = all_items

    def to_vec(self):
        return np.array([self.get(k, 0.0) for k in self._all_items])

    def update(self, items: dict):
        for k, v in items.items():
            if k not in self._all_items:
                raise ValueError(f"Invalid item: {repr(k)}")

            self.setdefault(k, 0.0)
            self[k] += v

class Plan:
    def __init__(self, official_name, since, to):
        self.official = Officials.get_official(official_name)
        self.since = since
        self.to = to

    @classmethod
    def of(cls, official_name):
        class initializer:
            def __init__(self, name):
                self.name = name
                self._since = {}
                self._to = {}

            def since(self, **kwargs):
                self._since = kwargs
                return self

            def to(self, **kwargs):
                self._to = kwargs
                return Plan(self.name, self._since, self._to)

        return initializer(official_name)

    def get_required_items(self):
        return (
            Officials
            .get_required_items_for(self.official.name)
            .since(**self.since)
            .to(**self.to)
        )

    def get_desc(self, with_required_items=False):
        ch_space = '\u3000'

        def dict_to_str(d):
            if d['elite_level'] == 0:
                e = ch_space * 2
            else:
                e = ' 一二三四'[d['elite_level']]
                e = f"精{e}"
            if not isinstance(d['skill_level'], int):
                s = tuple(d['skill_level'])
            else:
                s = d['skill_level']

            return f"{e} {d['level']:>2} 级（技能等级 {s}）"

        desc = f"把 {self.official.name:　<6} 从 {dict_to_str(self.since)} 升级到 {dict_to_str(self.to)}"
        if with_required_items:
            desc += '\n\t - 消耗：' + self.get_desc_for_required_items()

        return desc

    def get_desc_for_required_items(self):
        return ' '.join(
            f" {item}({amount:.2f})"
            for item, amount in self.get_required_items().items()
            if amount > 0
        )

class PlannerConfig(dict):
    default = {
        'ap_recovery_per_day': 240,
        'infra_money_per_day': 45000,
        'infra_midexpbook_per_day': 20,
        'disabled_path_keywords': [],
        'output_path': os.path.join(REPORT_PATH, f"arknights_{time.strftime('%Y%m%d%H%M%S')}.txt"),

        'cur_items': {},
        'target_items': {},
        'plans': [],

        'MAX_PLAN_DAYS': 1000,

        'display_plan_item_requirement': False,
        'display_path_item_change': False,
    }

    REG_ELITE_LV = r'^(精[一二])?\s*([1-9]([0-9]+)?)\s*级$'

    def __init__(self):
        super().__init__(self.default)

    def update_with_file(self, file):
        with open(file, 'r') as f:
            self.update_with_string(f.read())
        return self

    def update_with_string(self, string):
        config = yaml.load(string, Loader=yaml.FullLoader)

        # set config
        config_basic = config.get('规划设置', {})
        for config_key, yaml_key in {
            'ap_recovery_per_day': '每日回体',
            'infra_money_per_day': '每日基建龙门币',
            'infra_midexpbook_per_day': '每日基建中级作战录像',
        }.items():
            if yaml_key in config_basic:
                self[config_key] = float(config_basic.get(yaml_key))

        if '禁用规划路径' in config_basic:
            dps = config_basic.get('禁用规划路径') or ''
            self['disabled_path_keywords'] = dps.split()

        if '输出文件' in config_basic:
            output_path = config_basic['输出文件']
            output_path = output_path.replace('$TIMESTAMP', time.strftime('%Y%m%d%H%M%S'))
            self['output_path'] = output_path

        for config_key, yaml_key in {
            'display_plan_item_requirement': '显示提升目标消耗',
            'display_path_item_change': '显示路径材料变化',
        }.items():
            if yaml_key in config_basic:
                if config_basic[yaml_key] == '是':
                    self[config_key] = True
                elif config_basic[yaml_key] == '否':
                    self[config_key] = False
                else:
                    raise ValueError(
                        f"Unrecognized value for {yaml_key}: {config_basic[yaml_key]},"
                        f" valid: 是/否"
                    )

        # load cur item
        self['cur_items'] = self.parse_item_dict(config.get('持有道具', {}))
        self['cur_items']['1d'] = self['MAX_PLAN_DAYS']

        # load target items
        self['target_items'] = self.parse_item_dict(config.get('目标道具', {}))

        # load plans
        for plan in config['提升目标']:
            name, since, to = self.parse_plan_dict(plan)
            self['plans'].append(Plan.of(name).since(**since).to(**to))
        return self

    def parse_item_dict(self, item_dict):
        def parse_val(val_str):
            if isinstance(val_str, (int, float)):
                return val_str
            if any(val_str.endswith(unit) for unit in 'kwm'):
                val_str, unit = val_str[:-1], val_str[-1]
                unit = {'k': 1000, 'w': 1e4, 'm': 1e6}[unit]
            else:
                unit = 1
            return float(val_str) * unit

        cur_items = {k : parse_val(v) for k, v in item_dict.items()}
        if '龙门币' in cur_items:
            cur_items['1k龙门币'] = cur_items.pop('龙门币') / 1000.0
        return cur_items

    def parse_plan_dict(self, plan_dict):
        def parse_elite_level(lv_str):
            """
            Valid ones:
            "1级" "1 级" "精一1级" "精一 1级" "精二 40级"
            """
            if isinstance(lv_str, int):
                return 0, lv_str
            match = re.match(self.REG_ELITE_LV, lv_str.strip())
            if match is None:
                raise ValueError(f"Can not parse {repr(lv_str)} as character level")
            elv, lv, _ = match.groups()
            elv = {None: 0, '精一': 1, '精二': 2}[elv]
            lv = int(lv)
            return elv, lv

        def parse_skill_level(lv_str):
            if isinstance(lv_str, int):
                return lv_str
            lv_str = lv_str.strip()
            slv = [int(s.strip()) for s in lv_str.split(',')]
            return slv

        name = plan_dict['干员']

        elv, lv = parse_elite_level(plan_dict['当前状态']['等级'])
        slv = parse_skill_level(plan_dict['当前状态']['技能'])
        since = {'elite_level': elv, 'level': lv, 'skill_level': slv}

        elv, lv = parse_elite_level(plan_dict['目标状态']['等级'])
        slv = parse_skill_level(plan_dict['目标状态']['技能'])
        to = {'elite_level': elv, 'level': lv, 'skill_level': slv}
        return name, since, to

    def get_tradepath_for_daily_recovery(self):
        return TradePath({'1d': 1}, {
            '理智': self['ap_recovery_per_day'],
            '1k龙门币': self['infra_money_per_day'] / 1000,
            '中级作战记录': self['infra_midexpbook_per_day']
        }, "自然恢复 1 天")

    def get_tradepaths(self):
        if self['disabled_path_keywords']:
            dps = self['disabled_path_keywords']
            paths = [
                path for path in TRADE_PATHS
                if all(dp not in path.tag for dp in dps)
            ]
        else:
            paths = list(TRADE_PATHS)

        paths.append(self.get_tradepath_for_daily_recovery())
        return paths

    def get_cur_items(self):
        return self['cur_items']

    def get_target_items(self):
        return self['target_items']

    def get_plans(self):
        return self['plans']

class Planner:
    def __init__(self, all_items = ALL_ITEMS, all_paths = TRADE_PATHS):
        self._all_paths = list(TRADE_PATHS)
        self._all_items = all_items

        self.cur_items = Audit({}, self._all_items)
        self.target_items =  Audit({}, self._all_items)
        self.plans = []

        self.config = PlannerConfig()

    @property
    def n_paths(self):
        return len(self._all_paths)

    @property
    def n_items(self):
        return len(self._all_items)

    ##########################
    # User Input Getter
    ##########################
    def set_config(self, config):
        for k, v in config.items():
            assert k in self.config
            self.config[k] = v
        return self

    def add_trade_paths(self, *paths):
        self._all_paths.extend(paths)
        return self

    def add_cur_items(self, items):
        self.cur_items.update(items)
        return self

    def add_target_items(self, items):
        self.target_items.update(items)
        return self

    def add_plan(self, *plans):
        self.plans.extend(plans)
        for plan in plans:
            self.add_target_items(plan.get_required_items())
        return self

    def set_to_config(self, config):
        self.config.update_with_file(config)
        self._update_according_to_config()
        return self

    def set_to_config_string(self, config):
        self.config.update_with_string(config)
        self._update_according_to_config()
        return self

    def _update_according_to_config(self):
        self._all_paths = self.config.get_tradepaths()

        self.plans = self.config.get_plans()

        self.cur_items.clear()
        self.cur_items.update(self.config.get_cur_items())

        self.target_items.clear()
        self.add_target_items(self.config.get_target_items())
        for plan in self.plans:
            self.add_target_items(plan.get_required_items())

    ##########################
    # Core Logic
    ##########################
    def _linear_programming(self, c, A_ub, b_ub):
        """
        Minimize c @ x
        s.t. A_ub @x <= b_ub

        @param: c: N-d vector
        @param: A_ub: M x N matrix
        @param: b_ub: M-d vector
        @return: x: N-d vector
        """
        # optim_ret = scipy.optimize.linprog(method='simplex', c=c, A_ub=A_ub, b_ub=b_ub, options={'tol':1e-3})
        optim_ret = scipy.optimize.linprog(c=c, A_ub=A_ub, b_ub=b_ub)
        return optim_ret.x

    def _integer_linear_programming(self, c, A_ub, b_ub):
        """too slow, discarded"""
        # problem = pulp.LpProblem("<min_purchase>", pulp.LpMinimize)
        # path_cnt = pulp.LpVariable.dicts("path_cnt", range(P), 0, 10, pulp.LpInteger)
        # overflow = pulp.LpVariable.dicts("overflow", range(M), 0, 1000)

        # problem += pulp.lpDot(overflow.values(), overflow_punishment)

        # for m_ind in range(M):
        #     problem += pulp.lpDot(
        #         path_cnt.values(),
        #         path_gain[m_ind]
        #     ) == material_target[m_ind] + overflow[m_ind]

        # problem.solve()

        # for i in range(P):
        #     if path_cnt[i].varValue > 0:
        #         print(f"{path_cnt[i].varValue}: {self._all_paths[i]}")

        # for m in range(M):
        #     if overflow[m].varValue > 0:
        #         print(f"Item {ITEMS.to_name(m)} overflow: {overflow[m].varValue}")

    def get_path_return_matrix(self):
        """
        mat[i][j] means the gain of i-th item by executing the j-th path once
        positive the we gain the item, negative if the item is consumed
        """
        mat = np.zeros((self.n_items, self.n_paths))

        for p_ind, path in enumerate(self._all_paths):
            for item, cost in path.src.items():
                i_ind = self._all_items.to_id(item)
                mat[i_ind][p_ind] -= cost

            for item, gain in path.dst.items():
                i_ind = self._all_items.to_id(item)
                mat[i_ind][p_ind] += gain

        return mat

    def get_path_limit_matrixes(self):
        pl_A, pl_b = [], []
        path_limits = {'A_ub': pl_A, 'b_ub': pl_b}

        ind_for_1day = self._all_items.to_id('1d')
        zero_vec = [0] * self.n_paths

        def onehot(ind):
            vec = zero_vec[:]
            vec[ind] = 1
            return vec

        for p_ind, path in enumerate(self._all_paths):
            if path.max_cnt:
                pl_A.append(onehot(p_ind))
                pl_b.append(path.max_cnt)
            if path.max_cnt_per_day:
                pl_A.append(onehot(p_ind))
                pl_A[-1][ind_for_1day] = -path.max_cnt_per_day
                pl_b.append(0)

        return path_limits

    def deduce(self):
        # minimize 理智 = sum( apcost of a path * repeated time of the path )
        # s.t. sum( gain of a path * repeated time of the path ) >= target - cur

        P, I = self.n_paths, self.n_items

        path_return = self.get_path_return_matrix()
        target_items = self.target_items.to_vec() - self.cur_items.to_vec()

        assert path_return.shape == (I, P)
        assert target_items.shape == (I, )

        # add constraints for daily limit & max limit
        path_limits = self.get_path_limit_matrixes()

        # construct path weights s.t.
        # argmin path_weight @ path_cnt
        # = argmax timecost @ path_return @ path_cnt
        # = argmax timecost @ item_obtained
        # = argmax timecost @ item_obtained
        # = argmax 0.1 * obtained item '1d'
        timecost = np.zeros(target_items.size)
        timecost[self._all_items.to_id('1d')] = 10
        path_weight = -(timecost @ path_return)

        # construct linprog parameters
        A_ub = np.vstack([-path_return, path_limits['A_ub']]) # shape: (I+alpha, P)
        b_ub = np.hstack([-target_items, path_limits['b_ub']]) # shape: (I+alpha, )

        path_cnt = self._linear_programming(c=path_weight, A_ub=A_ub, b_ub=b_ub)

        self._scheme = Scheme(self, path_cnt, path_return)

    ##########################
    # Result Reporter
    ##########################
    def generate_report(self, file=None):
        if file is None:
            file = self.config['output_path']

        if '_scheme' not in self.__dict__:
            self.deduce()
        scheme = self._scheme

        with scheme.print_to_file(file, "w"):
            scheme.print_report()

    def print_report(self):
        self.generate_report(sys.stdout)
        return self

@dataclass
class Scheme:
    planner: Planner
    path_cnt: np.array
    path_return: np.array

    def get_obtained_items(self):
        path_gain = self.path_return.copy()
        path_gain[path_gain < 0] = 0
        return path_gain @ self.path_cnt

    def get_consumed_items(self):
        path_cons = self.path_return.copy()
        path_cons[path_cons > 0] = 0
        return -path_cons @ self.path_cnt

    def get_desc_for_path(self, path):
        d = lambda dict: list(dict)[0]

        if path.tag == '喂经验':
            return f"喂 {d(path.src)}"
        elif path.tag == '加工站':
            return f"加工站 造 {d(path.dst)}"
        elif path.tag == '贸易站':
            return f"贸易站 出售 {d(path.src)}"
        elif path.tag in (
            '采购凭证', '高级凭证', '资质凭证第一层', '资质凭证第二层', '资质凭证第三层'
        ) or path.tag.startswith('活动商店'):
            return f"{path.tag} 换 {d(path.dst)}"

        return path.tag

    def get_item_detail_for_path(self, path, path_cnt):
        detail = {'gain': '', 'cost': ''}
        items = defaultdict(lambda: 0.0)

        for item, amount in path.src.items():
            items[item] -= amount * path_cnt

        for item, amount in path.dst.items():
            items[item] += amount * path_cnt

        for item, amount in items.items():
            if amount > 0.1:
                detail['gain'] += f" {item}({amount:.2f})"
            elif amount < -0.1:
                detail['cost'] += f" {item}({-amount:.2f})"
        for key in 'gain', 'cost':
            if not detail[key]:
                detail[key] = '无'
        return detail

    def print_report(self):
        def section(title):
            self.print("=" * 20)
            self.print(title)
            self.print("=" * 20)

        def gap():
            self.print()

        obtained_items = self.get_obtained_items()
        consumed_items = self.get_consumed_items()
        cur_items = self.planner.cur_items.to_vec()
        target_items = self.planner.target_items.to_vec()

        all_items = self.planner._all_items
        config = self.planner.config

        section("结论")
        days = consumed_items[all_items.to_id('1d')]
        ap = int(days * config['ap_recovery_per_day']) + 1
        self.print(f" 为完成目标，至少需要 {ap} 理智，共需 {days:.2f} 天的自然恢复")

        gap()
        section("设置")
        self.print(f" 刀客塔每日自然回体为 {config['ap_recovery_per_day']}")
        self.print(
            f" 刀客塔的基建每日可供应 {config['infra_money_per_day']} 龙门币"
            f"和 {config['infra_midexpbook_per_day']} 中级作战录像"
        )
        if config['disabled_path_keywords']:
            self.print(f" 本次规划中禁用了包含以下关键字的路径: {','.join(self.planner.config['disabled_path_keywords'])}")
        else:
            self.print(f" 本次规划中没有禁用任何路径")

        gap()
        section("提升目标")
        for plan in self.planner.plans:
            self.print(f" {plan.get_desc()}")

        if self.planner.config['display_plan_item_requirement']:
            gap()
            section("提升目标（详细报告）")
            for plan in self.planner.plans:
                self.print(f" {plan.get_desc(with_required_items=True)}")

        gap()
        section("材料清单\n(结余 = 持有 + 获得 - 消耗 - 需求)")
        self.print("需求    持有     获得      消耗      结余     材料名")
        for t_cnt, c_cnt, obt_cnt, con_cnt, item in zip(
                target_items, 
                cur_items,
                obtained_items,
                consumed_items,
                all_items
            ):
            if item in ('理智', '1d'):
                continue
            if t_cnt > 0 or obt_cnt > 0.1 or con_cnt > 0.1:
                overflow = c_cnt + obt_cnt - con_cnt - t_cnt
                self.print(f"{int(t_cnt):5d} {int(c_cnt):5d} {obt_cnt:9.2f} {con_cnt:9.2f} {overflow:9.2f} {item}")

        gap()
        section("规划路径")
        self.print("重复次数   操作")
        for p_cnt, path in zip(self.path_cnt, self.planner._all_paths):
            if p_cnt > 0.1:
                path_desc = self.get_desc_for_path(path)
                self.print(f"{p_cnt:8.2f}  {path_desc}")

        if self.planner.config['display_path_item_change']:
            gap()
            section("规划路径（详细报告）")
            self.print("重复次数   操作")
            for p_cnt, path in zip(self.path_cnt, self.planner._all_paths):
                if p_cnt < 0.1:
                    continue
                path_desc = self.get_desc_for_path(path)
                path_detail = self.get_item_detail_for_path(path, p_cnt)
                self.print(f"{p_cnt:<8.2f}  {path_desc}")
                self.print(f"  - 获得： {path_detail['gain']}")
                self.print(f"  - 消耗： {path_detail['cost']}")

    def print(self, *args, **kwargs):
        kwargs['file'] = self._file
        print(*args, **kwargs)

    def print_to_file(self, filename, mode):
        class ctx_manager:
            def __enter__(this):
                if isinstance(filename, str):
                    self._file = open(filename, mode)
                else:
                    self._file = sys.stdout

            def __exit__(this, *args):
                if isinstance(filename, str):
                    self._file.close()
                else:
                    self._file = sys.stdout
        return ctx_manager()

if __name__ == '__main__':
    P = Planner(ALL_ITEMS)
    P.set_to_config('config.yaml')
    P.generate_report()
