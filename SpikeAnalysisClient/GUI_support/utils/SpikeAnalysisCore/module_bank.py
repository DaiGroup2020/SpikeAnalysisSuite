import warnings
warnings.filterwarnings('ignore')
import shutil
import time
from phy.apps.template import template_gui
import filecmp
import pprint
from timeit import default_timer
import os
import numpy as np
import pandas as pd


def post_curate_spikes(root_folder_input, experimenter, acquisition_system, mouse_id, recording_time, user_name, local=True):
    def ignore_recording_file(dir, files):
        files_to_ignore = ['recording.dat']
        return [file for file in files if file in files_to_ignore]
    time_start = default_timer()
    print('============================================================================')
    print('data: ', experimenter, acquisition_system, mouse_id, recording_time)
    print('POST CURATION MODULE')
    print('Routing...')
    if not root_folder_input.endswith('/'):
        source_root_folder = root_folder_input + '/'
    else:
        source_root_folder = root_folder_input
    source_sorting_result_folder = source_root_folder + experimenter + '/' + acquisition_system + '/' + mouse_id + \
                            '/' + recording_time + '/analysis/sorting_result/'
    source_post_curation_folder = source_sorting_result_folder + 'phy/'
    assert os.path.isdir(
        source_post_curation_folder), source_post_curation_folder + ' does not exist, please run sort_spikes before post curation. Or maybe no spikes are detected.'
    assert os.path.isfile(source_post_curation_folder+'spike_clusters.npy'), 'file not found: '+source_post_curation_folder+'spike_clusters.npy'
    assert os.path.isfile(source_post_curation_folder + 'cluster_group.tsv'), 'file not found: ' + source_post_curation_folder + 'cluster_group.tsv'
    source_sorting_metadata_path = source_sorting_result_folder + 'sorting_metadata.npy'
    assert os.path.isfile(
        source_sorting_metadata_path), source_sorting_metadata_path + 'does not exist, please run sort_spikes before post curation.'

    if local:
        print('copying data to local...')
        root_folder = os.path.expanduser('~') + '/Documents/SpikeAnalysisCache/'
        sorting_result_folder = root_folder + '/' + experimenter + '/' + acquisition_system + '/' + mouse_id + \
                                       '/' + recording_time + '/analysis/sorting_result/'
        post_curation_folder = sorting_result_folder + 'phy/'
        sorting_metadata_path = sorting_result_folder + 'sorting_metadata.npy'
        if os.path.exists(root_folder):
            shutil.rmtree(root_folder)
        os.makedirs(post_curation_folder)
        shutil.copytree(source_post_curation_folder, post_curation_folder, dirs_exist_ok=True)
        shutil.copyfile(source_sorting_metadata_path, sorting_metadata_path)
    else:
        sorting_result_folder = source_sorting_result_folder
        post_curation_folder = source_post_curation_folder
        sorting_metadata_path = source_sorting_metadata_path

    shutil.copyfile(post_curation_folder+'spike_clusters.npy', post_curation_folder+'spike_clusters_old.npy')
    shutil.copyfile(post_curation_folder + 'cluster_group.tsv', post_curation_folder + 'cluster_group_old.tsv')
    if os.path.exists(post_curation_folder+'params_preserve.py'):
        os.remove(post_curation_folder+'params_preserve.py')
    os.rename(post_curation_folder+'params.py', post_curation_folder+'params_preserve.py')
    with open(post_curation_folder+'params_preserve.py', 'r') as params_preserve:
        content = params_preserve.readlines()
        content[0] = "dat_path = r'" + post_curation_folder + "recording.dat'\n"
        with open(post_curation_folder+'params.py', 'a') as params:
            params.writelines(content)

    print('post curating...')
    modification_flag = False
    # template_gui(post_curation_folder+'params.py') # , clear_state=True, clear_cache=True
    os.system("phy template-gui "+post_curation_folder+"/params.py")
    if not filecmp.cmp(post_curation_folder+'spike_clusters.npy', post_curation_folder+'spike_clusters_old.npy') or not \
            filecmp.cmp(post_curation_folder+'cluster_group.tsv', post_curation_folder+'cluster_group_old.tsv'):
        modification_flag = True
        sorting_metadata = np.load(sorting_metadata_path, allow_pickle=True).item()
        cluster_group = pd.read_csv(post_curation_folder+'cluster_group.tsv', sep='\t')
        units_labels = cluster_group['group'].to_list()
        sorting_metadata['post_curation'] = True
        sorting_metadata['post_curation_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sorting_metadata['post_curator'] = os.environ['COMPUTERNAME']
        sorting_metadata['good_unit_number'] = units_labels.count('good')
        if 'unsorted' in units_labels:
            sorting_metadata['post_curation_accomplished'] = False
        else:
            sorting_metadata['post_curation_accomplished'] = True
        sorting_metadata['waveform_extraction_accomplished'] = False
        sorting_metadata['single_recording_figure_generation_accomplished'] = False
        sorting_metadata['single_recording_template_layout'] = None
        sorting_metadata['single_recording_unit_position'] = None
        sorting_metadata['single_recording_isi'] = None
        sorting_metadata['single_recording_cross_correlation'] = None
        sorting_metadata['single_recording_template_layout_parameters'] = None
        sorting_metadata['single_recording_unit_position_parameters'] = None
        sorting_metadata['single_recording_isi_parameters'] = None
        sorting_metadata['single_recording_cross_correlation_parameters'] = None
        np.save(sorting_metadata_path, sorting_metadata)
        post_curator = user_name
        if post_curator == '\n' or post_curator == '' or post_curator == None:
            print('no name input, use computer name instead')
        else:
            print('post curator: '+post_curator)
            sorting_metadata = np.load(sorting_metadata_path, allow_pickle=True).item()
            sorting_metadata['post_curator'] = post_curator
            np.save(sorting_metadata_path, sorting_metadata)
    else:
        modification_flag = False
        print('no modification, nothing changed')
    os.remove(post_curation_folder+'params.py')
    os.rename(post_curation_folder+'params_preserve.py', post_curation_folder+'params.py')
    if os.path.isfile(post_curation_folder+'spike_clusters_old.npy'):
        os.remove(post_curation_folder+'spike_clusters_old.npy')
    if os.path.isfile(post_curation_folder+'cluster_group_old.tsv'):
        os.remove(post_curation_folder+'cluster_group_old.tsv')
    if local and modification_flag:
        print('copying data to source...')
        # shutil.rmtree(source_post_curation_folder)
        shutil.copytree(post_curation_folder, source_post_curation_folder, ignore=ignore_recording_file, dirs_exist_ok=True)
        os.remove(source_sorting_metadata_path)
        shutil.copyfile(sorting_metadata_path, source_sorting_metadata_path)
    print('done')
    time_end = default_timer()
    print('Module time usage(s): ', time_end - time_start)

def read_sorting_metadata(root_folder_input, experimenter, acquisition_system, mouse_id, recording_time, display=False):
    if display:
        time_start = default_timer()
        print('============================================================================')
        print('data: ', experimenter, acquisition_system, mouse_id, recording_time)
        print('CHECK SORTING METADATA MODULE')
    if not root_folder_input.endswith('/'):
        root_folder_input = root_folder_input + '/'
    sorting_result_folder = root_folder_input + '/' + experimenter + '/' + acquisition_system + '/' + mouse_id + \
                      '/' + recording_time + '/analysis/sorting_result/'
    sorting_metadata_path = sorting_result_folder + 'sorting_metadata.npy'
    if os.path.isfile(sorting_metadata_path):
        sorting_metadata = np.load(sorting_metadata_path, allow_pickle=True).item()
    else:
        sorting_metadata = None
        if display:
            print(sorting_metadata_path + ' does not exist, please sort data before checking sorting metadata')
    if display:
        print('Sorting metadata is:')
        pprint.pprint(sorting_metadata)
        time_end = default_timer()
        print('Module time usage(s): ', time_end - time_start)
    return sorting_metadata

