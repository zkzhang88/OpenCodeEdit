import os
import logging
import csv
import numpy as np

import matplotlib.pyplot as plt

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def plot_embedding_scatter(embeddings_2d, title, xlabel=None, ylabel=None, figsize=(8, 6), 
                           point_size=3, alpha=0.7, save_path=None, show_fig=True):
    plt.figure(figsize=figsize)
    plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], s=point_size, alpha=alpha)
    plt.title(title)
    if xlabel is not None or ylabel is not None:
        if xlabel is not None:
            plt.xlabel(xlabel)
        if ylabel is not None:
            plt.ylabel(ylabel)
    plt.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200)
    log.info(f"Scatter plot saved to: {save_path}")
    if show_fig:
        plt.show()


def plot_embedding_scatter_with_labels(embeddings_2d, labels, title, xlabel=None, ylabel=None, 
                                      figsize=(8, 6), save_path=None, show_fig=True):
    """
    Plot embedding scatter with labels, using different shapes and colors for each label.
    
    Args:
        embeddings_2d: 2D embedding coordinates
        labels: Label for each point
        title: Chart title
        xlabel, ylabel: Axis labels
        figsize: Chart size
        point_size: Point size
        alpha: Transparency
        save_path: Save path
        show_fig: Whether to show the chart
    """
    plt.figure(figsize=figsize)
    
    # Define marker shapes and colors for different labels
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h', 'H', '+', 'x', '|', '_']
    colors = ['red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan',
              'magenta', 'yellow', 'black', 'navy', 'darkgreen']
    
    # Get unique labels
    unique_labels = list(set(labels))
    # Put None label at the end
    if None in unique_labels:
        unique_labels.remove(None)
        unique_labels.append(None)
    
    log.info(f"Plotting scatter, total {len(unique_labels)} labels: {unique_labels}")
    
    # Plot points for each label
    for i, label in enumerate(unique_labels):
    # Get indices for this label
        mask = np.array(labels) == label
        
        if label is None:
            # Points without label use default color and shape
            plt.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1], 
                       s=3, alpha=0.3, c="cornflowerblue", marker='o', 
                       label='Unlabeled')
        else:
            # Points with label use different color and shape
            marker = markers[i % len(markers)]
            color = colors[i % len(colors)]
            plt.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1], 
                       s=50, alpha=0.7, c=color, marker=marker, 
                       label=str(label), edgecolors='black', linewidth=0.5)
    
    plt.title(title)
    if xlabel is not None:
        plt.xlabel(xlabel)
    if ylabel is not None:
        plt.ylabel(ylabel)
    
    # Add legend
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches='tight')
        log.info(f"Scatter plot with labels saved to: {save_path}")
    if show_fig:
        plt.show()


def write_statistic_csv(csv_path, header, row):
    write_header = not os.path.exists(csv_path)
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(header)
        writer.writerow(row)