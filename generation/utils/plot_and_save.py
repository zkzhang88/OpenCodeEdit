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
        log.info(f"散点图已保存到: {save_path}")
    if show_fig:
        plt.show()


def plot_embedding_scatter_with_labels(embeddings_2d, labels, title, xlabel=None, ylabel=None, 
                                      figsize=(8, 6), save_path=None, show_fig=True):
    """
    绘制带标签的嵌入散点图，不同标签使用不同的形状和颜色
    
    Args:
        embeddings_2d: 2D嵌入坐标
        labels: 每个点对应的标签
        title: 图表标题
        xlabel, ylabel: 坐标轴标签
        figsize: 图表大小
        point_size: 点的大小
        alpha: 透明度
        save_path: 保存路径
        show_fig: 是否显示图表
    """
    plt.figure(figsize=figsize)
    
    # 定义不同标签对应的形状和颜色
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h', 'H', '+', 'x', '|', '_']
    colors = ['red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan',
              'magenta', 'yellow', 'black', 'navy', 'darkgreen']
    
    # 获取唯一标签
    unique_labels = list(set(labels))
    # 将None标签放在最后
    if None in unique_labels:
        unique_labels.remove(None)
        unique_labels.append(None)
    
    log.info(f"绘制散点图，共有 {len(unique_labels)} 种标签: {unique_labels}")
    
    # 为每种标签绘制点
    for i, label in enumerate(unique_labels):
        # 获取该标签对应的索引
        mask = np.array(labels) == label
        
        if label is None:
            # 没有标签的点使用默认颜色和形状
            plt.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1], 
                       s=3, alpha=0.3, c="cornflowerblue", marker='o', 
                       label='未标记')
        else:
            # 有标签的点使用不同颜色和形状
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
    
    # 添加图例
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=200, bbox_inches='tight')
        log.info(f"带标签的散点图已保存到: {save_path}")
    if show_fig:
        plt.show()


def write_statistic_csv(csv_path, header, row):
    write_header = not os.path.exists(csv_path)
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(header)
        writer.writerow(row)