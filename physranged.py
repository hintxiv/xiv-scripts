import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sb

if __name__ == '__main__':
    data = [
        ['Bard', 100, 22734.74],
        ['Dancer', 100, 23596.30],
        ['Machinist', 100, 22341.18],

        ['Bard', 99, 22074.53],
        ['Dancer', 99, 22381.10],
        ['Machinist', 99, 21866.17],

        ['Bard', 95, 21601.75],
        ['Dancer', 95, 21660.76],
        ['Machinist', 95, 21546.25],

        ['Bard', 90, 21303.97],
        ['Dancer', 90, 21185.83],
        ['Machinist', 90, 21343.91],

        ['Bard', 80, 20910.68],
        ['Dancer', 80, 20564.26],
        ['Machinist', 80, 21042.87],

        ['Bard', 70, 20575.52],
        ['Dancer', 70, 20123.12],
        ['Machinist', 70, 20761.01],

        ['Bard', 60, 20236.72],
        ['Dancer', 60, 19727.08],
        ['Machinist', 60, 20446.17],

        ['Bard', 50, 19869.09],
        ['Dancer', 50, 19342.84],
        ['Machinist', 50, 20108.73],

        ['Bard', 40, 19472.36],
        ['Dancer', 40, 18948.62],
        ['Machinist', 40, 19718.97],

        ['Bard', 30, 19032.97],
        ['Dancer', 30, 18516.90],
        ['Machinist', 30, 19268.36],
    ]

    df = pd.DataFrame(data, columns=['job', 'percentile', 'rdps'])
    

    plt.style.use('ggplot')
    plot = sb.relplot(
        data = df, 
        x="percentile", 
        y="rdps", 
        hue="job",  
        kind="line",
        palette={'Bard': '#91ba5e', 'Dancer': '#e2b0af', 'Machinist': '#6ee1d6'}
    )

    # Save the graph
    plot.savefig("plots/ranged_comparison.png")
