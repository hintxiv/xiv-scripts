import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sb

def calculate_cdh(damage, base_crit_rate, buff_crit_rate, crit_mod, base_dh_rate, buff_dh_rate, dh_mod = 1.25):
    crit_portion = damage * (1 - (1 / (crit_mod * dh_mod))) * (math.log(crit_mod) / (math.log(crit_mod * dh_mod)))
    dh_portion = damage * (1 - (1 / (crit_mod * dh_mod))) * (math.log(dh_mod) / (math.log(crit_mod * dh_mod)))

    dh_taxed = dh_portion * (buff_dh_rate / (base_dh_rate + buff_dh_rate))

    return dh_taxed

def calculate_dh(damage, base_dh_rate, buff_dh_rate, dh_mod = 1.25):
    dh_taxed = damage * (1 - (1 / dh_mod)) * (buff_dh_rate / (base_dh_rate + buff_dh_rate))

    #print(f'DH! Damage: {damage}\n taxed: {dh_taxed}\n\n\n')

    return dh_taxed


def simulate_rdps(hits, base_crit_rate, buff_crit_rate, crit_mod, base_dh_rate, buff_dh_rate, dh_mod = 1.25):
    crit_rate = base_crit_rate + buff_crit_rate
    dh_rate = base_dh_rate + buff_dh_rate
    damage = 0

    for hit in hits:
        damage_roll = hit * np.random.uniform(0.95, 1.05)

        is_crit = np.random.uniform() < crit_rate
        is_dh = np.random.uniform() < dh_rate

        if is_crit and is_dh:
            damage += calculate_cdh(damage_roll * crit_mod * dh_mod, base_crit_rate, buff_crit_rate, crit_mod, base_dh_rate, buff_dh_rate)

        elif is_dh:
            damage += calculate_dh(damage_roll * dh_mod, base_dh_rate, buff_dh_rate)

        else:
            pass
            #print("No DH, skip")

    return damage / len(hits)

def make_dataset(hits, base_crit_rate, buff_crit_rate, crit_mod, base_dh_rate, buff_dh_rate, iters = 5000):
    df = pd.DataFrame(columns=['iter', 'rdps'])

    for i in range(iters):
        rdps = simulate_rdps(hits, base_crit_rate, buff_crit_rate, crit_mod, base_dh_rate, buff_dh_rate)
        df.loc[i] = [i] + [rdps]

    return df

if __name__ == '__main__':
    # Setup a list of "hits" (damage) in a MCH opener from a random log
    hits = [34700] * 5 + [93600] + [17900] * 5 + [10200] * 7 + [69000] + [47300] + [14900]
    hits = [ hit / 1.3 for hit in hits ]  # arbitrary buff dampening lol

    # Make datasets for the no BL case and the BL case
    no_bl = make_dataset(hits = hits, base_crit_rate = 0.258, buff_crit_rate = 0, crit_mod = 1.608, base_dh_rate = 0.426, buff_dh_rate = 0.2)
    bl = make_dataset(hits = hits, base_crit_rate = 0.258, buff_crit_rate = 0.1, crit_mod = 1.608, base_dh_rate = 0.426, buff_dh_rate = 0.2)

    # Merge datasets and plot
    concatenated = pd.concat([no_bl.assign(case='no crit buffs'), bl.assign(case='battle litany')])

    plt.style.use('ggplot')
    plot = sb.scatterplot(
        data = concatenated, 
        x="iter", 
        y="rdps",
        s=2,
        hue="case",  
        palette={'no crit buffs': '#F8766D', 'battle litany': '#00BFC4'}
    )
    plot.set(ylabel="battle voice contrib.")

    # Compute 50th quantile in each case
    no_buffs_high_roll = no_bl.quantile(.5).rdps
    buffs_high_roll = bl.quantile(.5).rdps

    plot.axhline(y=no_buffs_high_roll, color='#F8766D', linewidth=0.8)
    plot.axhline(y=buffs_high_roll, color='#00BFC4', linewidth=0.8)

    #for line in plot.lines:
    #    y = line.get_ydata()[-1]
    #    plot.annotate('Median', xy=(1, y + 100), color='black')

    print(f"Battle voice contrib. without BL (median): {no_buffs_high_roll}")
    print(f"Battle voice contrib. with BL (median): {buffs_high_roll}")

    # Save the graph
    plot.get_figure().savefig("plot.png")
