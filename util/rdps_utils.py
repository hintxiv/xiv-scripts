import numpy as np
from copy import deepcopy
from dataclasses import dataclass
from math import floor, log
from typing import List

@dataclass(frozen=True)
class Buff:
    crit: float = 0
    dh: float = 0
    mod: float = 1

@dataclass
class Stats:
    base_crit_rate: float
    crit_rate: float
    crit_mod: float
    base_dh_rate: float
    dh_rate: float
    dh_mod: float = 1.25
    mod: float = 1

    def __add__(self, buff: Buff):
        """Stats + Buff = Stats w/ Buff's Modifiers"""
        new_stats = deepcopy(self)
        new_stats.crit_rate = min(self.crit_rate + buff.crit, 1)
        new_stats.dh_rate = min(self.dh_rate + buff.dh, 1)
        new_stats.mod *= buff.mod
        return new_stats

def calculate_cdh(damage: int, b: Buff, s: Stats) -> int:
    crit_portion = damage * (1 - (1 / (s.crit_mod * s.dh_mod))) * (log(s.crit_mod) / log(s.crit_mod * s.dh_mod))
    dh_portion = damage * (1 - (1 / (s.crit_mod * s.dh_mod))) * (log(s.dh_mod) / log(s.crit_mod * s.dh_mod))

    crit_contrib = crit_portion * (b.crit / s.crit_rate) * (1 - ((1 - (1 / (s.crit_mod * s.mod)))) * (log(s.mod) / log(s.crit_mod * s.mod)))
    dh_contrib = dh_portion * (b.dh / s.dh_rate) * (1 - (1 - ((1 / (s.dh_mod * s.mod)))) * (log(s.mod) / log(s.dh_mod * s.mod)))

    # What the fuck.
    if b.mod > 1:
        mc_unbuffed = ((1 / (s.crit_mod * s.dh_mod)) + ((1 - (1 / (s.crit_mod * s.dh_mod))) * (log(s.crit_mod) / log(s.crit_mod * s.dh_mod)) * (s.base_crit_rate / s.crit_rate)) \
            + ((1 - (1 / (s.crit_mod * s.dh_mod))) * (log(s.dh_mod) / log(s.crit_mod * s.dh_mod)) * (s.base_dh_rate / s.dh_rate))) * (1 - (1 / s.mod)) * (log(b.mod) / log(s.mod))

        mc_crit = ((1 - (1 / (s.crit_mod * s.dh_mod))) * (log(s.crit_mod) / log(s.crit_mod * s.dh_mod)) * ((s.crit_rate - s.base_crit_rate) / s.crit_rate)) \
            * (1 - (1 / (s.crit_mod * s.mod))) * (log(b.mod) / log(s.crit_mod * s.mod))

        mc_dh = ((1 - (1 / (s.crit_mod * s.dh_mod))) * (log(s.dh_mod) / log(s.crit_mod * s.dh_mod)) * ((s.dh_rate - s.base_dh_rate) / s.dh_rate)) \
            * (1 - (1 / (s.dh_mod * s.mod))) * (log(b.mod) / log(s.dh_mod * s.mod))

        mod_contrib = damage * (mc_unbuffed + mc_crit + mc_dh)

    else:
        mod_contrib = 0

    return floor(crit_contrib + dh_contrib + mod_contrib)

def calculate_crit(damage: int, b: Buff, s: Stats) -> int:
    crit_portion = damage * (1 - (1 / s.crit_mod))
    crit_contrib = crit_portion * (b.crit / s.crit_rate) * (1 - (1 - (1 / (s.crit_mod * s.mod))) * (log(s.mod) / log(s.crit_mod * s.mod)))

    if b.mod > 1:
        mc_unbuffed = ((1 / s.crit_mod) + (1 - (1 / (s.crit_mod))) * (s.base_crit_rate / s.crit_rate)) * (1 - (1 / s.mod)) * (log(b.mod) / log(s.mod))
        mc_buffed = (1 - (1 / (s.crit_mod))) * ((s.crit_rate - s.base_crit_rate) / s.crit_rate) * (1 - (1 / (s.crit_mod * s.mod))) * (log(b.mod) / log(s.crit_mod * s.mod))
        mod_contrib = damage * (mc_unbuffed + mc_buffed)

    else:
        mod_contrib = 0

    return floor(crit_contrib + mod_contrib)

def calculate_dh(damage: int, b: Buff, s: Stats) -> int:
    dh_portion = damage * (1 - (1 / s.dh_mod))
    dh_contrib = dh_portion * (b.dh / s.dh_rate) * (1 - (1 - (1 / (s.dh_mod * s.mod))) * (log(s.mod) / log(s.dh_mod * s.mod)))

    if b.mod > 1:
        mc_unbuffed = ((1 / s.dh_mod) + (1 - (1 / (s.dh_mod))) * (s.base_dh_rate / s.dh_rate)) * (1 - (1 / s.mod)) * (log(b.mod) / log(s.mod))
        mc_buffed = (1 - (1 / (s.dh_mod))) * ((s.dh_rate - s.base_dh_rate) / s.dh_rate) * (1 - (1 / (s.dh_mod * s.mod))) * (log(b.mod) / log(s.dh_mod * s.mod))
        mod_contrib = damage * (mc_unbuffed + mc_buffed)

    else:
        mod_contrib = 0

    return floor(dh_contrib + mod_contrib)

def calculate_none(damage, b: Buff, s: Stats) -> int:
    if b.mod > 1:
        mod_contrib = damage * (1 - (1 / s.mod)) * (log(b.mod) / log(s.mod))
        return floor(mod_contrib)

    return 0

def simulate_rdps_buffed(hits: List[int], time: int, buffs: List[Buff], stats: Stats) -> float:
    damage = 0
    for hit in hits:
        damage_roll = hit * np.random.uniform(0.95, 1.05)
        is_crit = np.random.uniform() < stats.crit_rate
        is_dh = np.random.uniform() < stats.dh_rate

        if is_crit and is_dh:
            hit = floor(damage_roll * stats.crit_mod * stats.dh_mod * stats.mod)
            unbuffed_damage = 0 + hit
            for buff in buffs:
                unbuffed_damage -= calculate_cdh(hit, buff, stats)

        elif is_crit:
            hit = floor(damage_roll * stats.crit_mod * stats.mod)
            unbuffed_damage = 0 + hit
            for buff in buffs:
                unbuffed_damage -= calculate_crit(hit, buff, stats)

        elif is_dh:
            hit = floor(damage_roll * stats.dh_mod * stats.mod)
            unbuffed_damage = 0 + hit
            for buff in buffs:
                unbuffed_damage -= calculate_dh(hit, buff, stats)

        else:
            hit = floor(damage_roll * stats.mod)
            unbuffed_damage = 0 + hit
            for buff in buffs:
                unbuffed_damage -= calculate_none(hit, buff, stats)

        damage += unbuffed_damage

    return damage / time
 
def simulate_rdps_buffer(hits: List[int], time: int, buff: Buff, stats: Stats) -> float:
    damage = 0
    for hit in hits:
        damage_roll = hit * np.random.uniform(0.95, 1.05)
        is_crit = np.random.uniform() < stats.crit_rate
        is_dh = np.random.uniform() < stats.dh_rate

        if is_crit and is_dh:
            hit = floor(damage_roll * stats.crit_mod * stats.dh_mod * stats.mod)
            damage += calculate_cdh(hit, buff, stats)

        elif is_crit:
            hit = floor(damage_roll * stats.crit_mod * stats.mod)
            damage += calculate_crit(hit, buff, stats)

        elif is_dh:
            hit = floor(damage_roll * stats.dh_mod * stats.mod)
            damage += calculate_dh(hit, buff, stats)

        else:
            hit = floor(damage_roll * stats.mod)
            damage += calculate_none(hit, buff, stats)

    return damage / time
