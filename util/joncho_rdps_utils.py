import numpy as np
from math import floor, log
from typing import List
from .rdps_utils import Buff, Stats

def calculate_cdh(damage: int, b: Buff, s: Stats) -> int:
    mc = s.crit_mod
    md = s.dh_mod
    mi = b.mod
    m = s.mod
    ci = b.crit
    cb = s.crit_rate
    cu = s.base_crit_rate
    di = b.dh
    db = s.dh_rate
    du = s.base_dh_rate

    crit_contrib = (1 - 1/(mc*md*m)) * (log(mc)/log(mc*md*m)) * (ci/cb)*((db-du)/db) + \
            (1 - 1/(mc*m)) * (log(mc)/log(mc*m)) * (ci/cb)*(du/db)

    dh_contrib = (1 - 1/(mc*md*m)) * (log(md)/log(mc*md*m)) * (di/db)*((cb-cu)/cb) + \
            (1 - 1/(md*m)) * (log(md)/log(md*m)) * (di/db)*(cu/cb)

    if mi > 1:
        mod_contrib = (((cb-cu)/cb)*((db-du)/db)*(1 - (1/(mc*md*m)))*(log(m)/log(mc*md*m)) + \
                ((cb-cu)/cb)*(du/db)*(1 - (1/(mc*m)))*(log(m)/log(mc*m)) + \
                (cu/cb)*((db-du)/db)*(1 - (1/(md*m)))*(log(m)/log(md*m)) + \
                (cu/cb)*(du/db)*(1 - (1/m))*(log(mi)/log(m)))
    else: 
        mod_contrib = 0

    return floor(damage * (crit_contrib + dh_contrib + mod_contrib))

def calculate_crit(damage: int, b: Buff, s: Stats) -> int:
    mc = s.crit_mod
    md = s.dh_mod
    mi = b.mod
    m = s.mod
    ci = b.crit
    cb = s.crit_rate
    cu = s.base_crit_rate

    crit_contrib = (1 - 1/(mc*m)) * (log(mc)/log(mc*m)) * (ci/cb)

    if mi > 1:
        mod_contrib = (cu/cb)*(1 - (1/m))*(log(mi)/log(m)) + ((cb-cu)/cb)*(1 - (1/(mc*m)))*(log(m)/log(mc*m))    
    else:
        mod_contrib = 0

    return floor(damage * (crit_contrib + mod_contrib))

def calculate_dh(damage: int, b: Buff, s: Stats) -> int:
    mc = s.crit_mod
    md = s.dh_mod
    mi = b.mod
    m = s.mod
    di = b.dh
    db = s.dh_rate
    du = s.base_dh_rate

    dh_contrib = (1 - 1/(md*m)) * (log(md)/log(md*m)) * (di/db)

    if mi > 1:
        mod_contrib = (du/db)*(1 - (1/m))*(log(mi)/log(m)) + ((db-du)/db)*(1 - (1/(md*m)))*(log(m)/log(md*m))
    else:
        mod_contrib = 0

    return floor(damage * (dh_contrib + mod_contrib))

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

if __name__ == "__main__":
    print("Sanity check for Joncho's rDPS formula")

    hit = 110550

    # i530 bis
    mch_stats = Stats(
        mod = 1,
        base_crit_rate = 0.258,
        crit_rate = 0.258,
        crit_mod = 1.608,
        base_dh_rate = 0.426,
        dh_rate = 0.426,
    )

    # Some buffs to play with
    BattleVoice = Buff(dh = 0.2)
    TrickAttack = Buff(mod = 1.05)
    BattleLitany = Buff(crit = 0.1)
    Devilment = Buff(crit = 0.2, dh = 0.2)

    mch_stats += BattleLitany
    mch_stats += TrickAttack
    mch_stats += BattleVoice
    mch_stats += Devilment

    print(mch_stats)

    print(f"BL: {calculate_cdh(hit, BattleLitany, mch_stats)}")
    print(f"DM: {calculate_cdh(hit, Devilment, mch_stats)}")
    print(f"BV: {calculate_cdh(hit, BattleVoice, mch_stats)}")
    print(f"TA: {calculate_cdh(hit, TrickAttack, mch_stats)}")
