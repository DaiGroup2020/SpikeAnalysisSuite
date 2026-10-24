import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import matplotlib.ticker as ticker
import os
import spikeinterface.postprocessing as spost
import pandas as pd

def template_layout_plot(waveform, sorting, sorting_metadata, unit_color_map, subfigure_folder, uv_per_um_scale=1, ms_per_um_scale=1 / 20, zoom_scale=1.2, scale_bar_ms=1, scale_bar_uv=100, scale_bar_margin=40):
    channel_circle_radius = 10
    sampling_frequency = sorting.get_sampling_frequency()
    unit_ids = sorting.get_unit_ids()
    if not subfigure_folder.endswith('/'):
        subfigure_folder = subfigure_folder + '/'
    if not os.path.exists(subfigure_folder):
        os.makedirs(subfigure_folder)
    assert len(unit_ids) == len(unit_color_map), 'Number of units detected '+str(len(unit_ids))+' should match number of unit color used '+str(len(unit_color_map))
    all_channel_positions = sorting_metadata['layout'].tolist()
    preserved_channel_positions = waveform.get_channel_locations().tolist()
    for unit_id, unit_color in zip(unit_ids, unit_color_map):
        templates = waveform.get_template(unit_id=unit_id, mode='median')
        templates_std = waveform.get_template(unit_id=unit_id, mode='std')
        plt.figure()
        ax = plt.gca()
        for channel_position in all_channel_positions:
            if channel_position in preserved_channel_positions:
                pad_patch = Circle(channel_position, channel_circle_radius, edgecolor=(0.9, 0.7, 0.1), facecolor='yellow', zorder=1)
            else:
                pad_patch = Circle(channel_position, channel_circle_radius, edgecolor='grey', facecolor='white', zorder=1)
            ax.add_patch(pad_patch)
        for preserved_channel_ind, preserved_channel_position in enumerate(preserved_channel_positions):
            template_per_channel = templates[:, preserved_channel_ind]
            template_std_per_channel = templates_std[:, preserved_channel_ind]
            x = (np.array(range(len(template_per_channel))) - int(
                len(template_per_channel) / 2)) / sampling_frequency * 1000 / ms_per_um_scale + preserved_channel_position[0]
            y = template_per_channel/uv_per_um_scale+preserved_channel_position[1]
            y_std = template_std_per_channel/uv_per_um_scale
            y_upper_shade = y+y_std
            y_lower_shade = y-y_std
            ax.fill_between(x, y_lower_shade, y_upper_shade, color=(0.5, 0.5, 0.5, 0.1), zorder=2)
            ax.plot(x, y, color=unit_color, zorder=3)
        xlim = np.array(ax.get_xlim())
        xlim = zoom_scale*xlim+(1-zoom_scale)*np.average(xlim)
        ylim = np.array(ax.get_ylim())
        ylim = zoom_scale * ylim + (1 - zoom_scale) * np.average(ylim)
        plt.xlim(xlim)
        plt.ylim(ylim)
        plt.plot([xlim[0] + scale_bar_margin, xlim[0] + scale_bar_margin + scale_bar_ms / ms_per_um_scale], [ylim[0] + scale_bar_margin, ylim[0] + scale_bar_margin], zorder=4, color='black')
        plt.text(xlim[0] + scale_bar_margin + 0.5 * (scale_bar_ms / ms_per_um_scale), ylim[0] + 0.5 * scale_bar_margin, str(scale_bar_ms) + 'ms', fontsize=7, ha='center', va='center', color='black', zorder=4)
        plt.plot([xlim[0]+scale_bar_margin, xlim[0]+scale_bar_margin], [ylim[0]+scale_bar_margin, ylim[0]+scale_bar_margin+scale_bar_uv / uv_per_um_scale], zorder=5, color='black')
        plt.text(xlim[0] + 0.5 * scale_bar_margin, ylim[0] + scale_bar_margin + 0.5 * (scale_bar_uv / uv_per_um_scale), str(scale_bar_uv) + 'uV', fontsize=7, ha='center', va='center', color='black', rotation=90, zorder=4)
        plt.tick_params(axis='both', which='both', bottom=True, top=True, right=True, labelbottom=True, labeltop=True,
                        labelright=True)
        plt.tight_layout(pad=3.0)
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(n=5))
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=5))
        ax.set_box_aspect((ylim[1]-ylim[0])/(xlim[1]-xlim[0]))
        plt.title('Unit '+str(unit_id))
        figure_path = subfigure_folder+'Unit_'+str(unit_id)+'.svg'
        plt.savefig(figure_path, format='svg', dpi=300)

def unit_position_plot(waveform, sorting_metadata, unit_color_map, subfigure_folder, zoom_scale=1.2):
    channel_circle_radius = 10
    unit_circle_radius = 10
    unit_positions = spost.compute_unit_locations(waveform, load_if_exists=True)
    if not subfigure_folder.endswith('/'):
        subfigure_folder = subfigure_folder + '/'
    if not os.path.exists(subfigure_folder):
        os.makedirs(subfigure_folder)
    assert len(unit_positions) == len(unit_color_map), 'Number of units detected ' + str(
        len(unit_positions)) + ' should match number of unit color used ' + str(len(unit_color_map))
    all_channel_positions = sorting_metadata['layout'].tolist()
    preserved_channel_positions = waveform.get_channel_locations().tolist()
    plt.figure()
    ax = plt.gca()
    for channel_position in all_channel_positions:
        if channel_position in preserved_channel_positions:
            pad_patch = Circle(channel_position, channel_circle_radius, edgecolor=(0.9, 0.7, 0.1), facecolor='yellow', zorder=1)
        else:
            pad_patch = Circle(channel_position, channel_circle_radius, edgecolor='grey', facecolor='white', zorder=1)
        ax.add_patch(pad_patch)
    for unit_position, unit_color in zip(unit_positions, unit_color_map):
        unit_patch = Circle(unit_position, unit_circle_radius, edgecolor=unit_color, facecolor=unit_color, zorder=2)
        ax.add_patch(unit_patch)
    all_channel_positions = np.array(all_channel_positions)
    x_min = min(np.min(all_channel_positions[:, 0])-channel_circle_radius, np.min(unit_positions[:, 0])-unit_circle_radius)
    x_max = max(np.max(all_channel_positions[:, 0]) + channel_circle_radius,
                   np.max(unit_positions[:, 0]) + unit_circle_radius)
    y_min = min(np.min(all_channel_positions[:, 1]) - channel_circle_radius,
                   np.min(unit_positions[:, 1]) - unit_circle_radius)
    y_max = max(np.max(all_channel_positions[:, 1]) + channel_circle_radius,
                   np.max(unit_positions[:, 1]) + unit_circle_radius)
    xlim = np.array([x_min, x_max])
    xlim = zoom_scale * xlim + (1 - zoom_scale) * np.average(xlim)
    ylim = np.array([y_min, y_max])
    ylim = zoom_scale * ylim + (1 - zoom_scale) * np.average(ylim)
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.tick_params(axis='both', which='both', bottom=True, top=True, right=True, labelbottom=True, labeltop=True,
                    labelright=True)
    plt.tight_layout(pad=3.0)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(n=5))
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(n=5))
    ax.set_box_aspect((ylim[1] - ylim[0]) / (xlim[1] - xlim[0]))
    plt.title('Unit Position')
    figure_path = subfigure_folder + 'unit_position.svg'
    plt.savefig(figure_path, format='svg', dpi=300)

def isi_plot(waveform, sorting, unit_color_map, subfigure_folder, inter_bar_margin_ratio=0.8, ncol=5):
    if not subfigure_folder.endswith('/'):
        subfigure_folder = subfigure_folder + '/'
    if not os.path.exists(subfigure_folder):
        os.makedirs(subfigure_folder)
    (hist_all, edge) = spost.compute_isi_histograms(waveform, load_if_exists=True)
    assert hist_all.shape[0] == len(unit_color_map), 'Number of units detected ' + str(
        hist_all.shape[0]) + ' should match number of unit color used ' + str(len(unit_color_map))
    unit_ids = sorting.get_unit_ids()
    assert len(unit_ids) == len(unit_color_map), 'Number of units detected ' + str(
        len(unit_ids)) + ' should match number of unit color used ' + str(len(unit_color_map))
    x = [(a + edge[i + 1]) / 2.0 for i, a in enumerate(edge[0:-1])]
    hist_all = hist_all/np.sum(hist_all, axis=1)[:, np.newaxis]*100
    for (unit_ind, (unit_id, unit_color)) in enumerate(zip(unit_ids, unit_color_map)):
        plt.figure()
        hist = hist_all[unit_ind, :]
        plot_data = pd.Series(hist, x)
        width = abs(plot_data.index[1]) - abs(plot_data.index[0])
        plt.bar(plot_data.index, plot_data.values, width=inter_bar_margin_ratio * width, color=unit_color, align='center')
        plt.xlabel('Interval ms')
        plt.ylabel('Percentage %')
        plt.title('Unit ' + str(unit_id))
        figure_path = subfigure_folder + 'Unit_' + str(unit_id) + '.svg'
        plt.savefig(figure_path, format='svg', dpi=300)
    nrow = int(np.ceil(len(unit_ids)/ncol))
    fig, axs = plt.subplots(nrow, ncol)
    for row in range(nrow):
        for col in range(ncol):
            if nrow == 1:
                sub_axs = axs[col]
            else:
                sub_axs = axs[row, col]
            unit_ind = row*ncol+col
            if unit_ind < len(unit_ids):
                unit_color = unit_color_map[unit_ind]
                hist = hist_all[unit_ind, :]
                plot_data = pd.Series(hist, x)
                width = abs(plot_data.index[1]) - abs(plot_data.index[0])
                sub_axs.bar(plot_data.index, plot_data.values, width=inter_bar_margin_ratio * width, color=unit_color, align='center')
            sub_axs.axis('off')
    plt.suptitle('All Units')
    figure_path = subfigure_folder + 'All_units.svg'
    plt.savefig(figure_path, format='svg', dpi=300)




def correlation_plot(waveform, sorting, unit_color_map, subfigure_folder, inter_bar_margin_ratio=0.8):
    if not subfigure_folder.endswith('/'):
        subfigure_folder = subfigure_folder + '/'
    if not os.path.exists(subfigure_folder):
        os.makedirs(subfigure_folder)
    (ccg, edge) = spost.compute_correlograms(waveform, load_if_exists=True)
    assert ccg.shape[0] == len(unit_color_map), 'Number of units detected ' + str(
        ccg.shape[0]) + ' should match number of unit color used ' + str(len(unit_color_map))
    unit_ids = sorting.get_unit_ids()
    assert len(unit_ids) == len(unit_color_map), 'Number of units detected ' + str(
        len(unit_ids)) + ' should match number of unit color used ' + str(len(unit_color_map))
    x = [(a + edge[i + 1]) / 2.0 for i, a in enumerate(edge[0:-1])]
    for (unit_ind, (unit_id, unit_color)) in enumerate(zip(unit_ids, unit_color_map)):
        plt.figure()
        hist = ccg[unit_ind, unit_ind, :]
        hist = hist/np.max(hist)
        plot_data = pd.Series(hist, x)
        width = abs(plot_data.index[1]) - abs(plot_data.index[0])
        plt.bar(plot_data.index, plot_data.values, width=inter_bar_margin_ratio * width, color=unit_color, align='center')
        plt.xlabel('Shift ms')
        plt.ylabel('Coefficient')
        plt.title('Unit ' + str(unit_id))
        figure_path = subfigure_folder + 'Unit_' + str(unit_id) + '.svg'
        plt.savefig(figure_path, format='svg', dpi=300)
    fig, axs = plt.subplots(len(unit_ids), len(unit_ids))
    for unit_ind1, unit_id1 in enumerate(unit_ids):
        for unit_ind2, unit_id2 in enumerate(unit_ids):
            sub_axs = axs[unit_ind1, unit_ind2]
            if unit_ind1 == unit_ind2:
                unit_color = unit_color_map[unit_ind1]
            else:
                unit_color = (0.5, 0.5, 0.5)
            hist = ccg[unit_ind1, unit_ind2, :]
            hist = hist / np.max(hist)
            plot_data = pd.Series(hist, x)
            width = abs(plot_data.index[1]) - abs(plot_data.index[0])
            sub_axs.bar(plot_data.index, plot_data.values, width=inter_bar_margin_ratio * width, color=unit_color, align='center')
            sub_axs.axis('off')
    plt.suptitle('All Units')
    figure_path = subfigure_folder + 'All_units.svg'
    plt.savefig(figure_path, format='svg', dpi=300)



