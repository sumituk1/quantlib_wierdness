import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import cm as cm
sns.set(context="paper", font="monospace")

def plot_correlation(corr, labels):
    # Load the datset of correlations between cortical brain networks
    # df = sns.load_dataset("brain_networks", header=[0, 1, 2], index_col=0)
    # corrmat = df.corr()

    # Set up the matplotlib figure
    f, ax = plt.subplots(figsize=(12, 9))

    # Draw the heatmap using seaborn
    sns.heatmap(corr, vmax=.8, square=True)

    # Use matplotlib directly to emphasize known networks
    # networks = data.columns.get_level_values("network")

    plt.xticks(range(len(labels)), labels)
    plt.yticks(range(len(labels)), labels)
    plt.matshow(corr)
    # for i, network in enumerate(corr):
    #     # if i and network != networks[i - 1]:
    #     ax.axhline(network, c="w")
    #     ax.axvline(network.T, c="w")


    f.tight_layout()