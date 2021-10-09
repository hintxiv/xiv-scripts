import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sb

from copy import deepcopy
from dataclasses import dataclass
from math import floor, log
from typing import List

from util.rdps_utils import *

def make_dataset(hits: List[int], buffs: List[Buff], stats: Stats, time = 20, iters = 10000) -> pd.DataFrame:
    df = pd.DataFrame(columns=['iter', 'rdps'])

    buffed_stats = stats
  
    for buff in buffs:
        buffed_stats += buff

    for i in range(iters):
        rdps = simulate_rdps_buffed(hits, time, buffs, buffed_stats)
        df.loc[i] = [i] + [rdps]

    return df

if __name__ == '__main__':
    # Quick and dirty "machinist opener"
    hits = [34700] * 5 + [93600] + [17900] * 5 + [10200] * 7 + [69000] + [47300] + [14900]
    hits = [ floor(hit / 1.3) for hit in hits ]  # arbitrary buff dampening lol

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

    no_buffs = make_dataset(hits, [], mch_stats)
    bv = make_dataset(hits, [BattleVoice], mch_stats)
    bv_litany = make_dataset(hits, [BattleVoice, BattleLitany], mch_stats)
    bv_trick = make_dataset(hits, [BattleVoice, TrickAttack], mch_stats)
    bv_litany_dm_trick = make_dataset(hits, [BattleVoice, BattleLitany, Devilment, TrickAttack], mch_stats)

    # Merge sets and plot
    concatenated = pd.concat([
        no_buffs.assign(case='None'),
        bv.assign(case='BV'), 
        bv_litany.assign(case='BV + BL'),
        bv_trick.assign(case='BV + TA'),
        bv_litany_dm_trick.assign(case='BV + BL + DM + TA'),
    ])

    plt.style.use('ggplot')
    plot = sb.boxplot(
        data = concatenated,
        x = "case",
        y = "rdps",
    )
    plot.set(xlabel="buff combination", ylabel="MCH's rdps (fudged damage #s)")

    # Numerical summaries
    print("None")
    print(no_buffs.describe().rdps)
    print("\nBV")
    print(bv.describe().rdps)
    print("\nBV + BL")
    print(bv_litany.describe().rdps)
    print("\nBV + TA")
    print(bv_trick.describe().rdps)
    print("\nBV + BL + DM + TA")
    print(bv_litany_dm_trick.describe().rdps)

    plot.get_figure().savefig("plots/bv_rdps.png")
