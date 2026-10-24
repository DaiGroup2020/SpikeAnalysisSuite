from .NetworkUtils import pack, unpack, Envelope, MySocket
from .ProcessUtils import SpikeAnalysisProcess
from .SpikeAnalysisCore.module_bank import post_curate_spikes
from PyQt5.QtWidgets import QApplication
from pprint import pprint
import time
import multiprocessing
import traceback


def listen_tasks_from_server(package, **kwargs):
    try:
        client_addr = (package.client_ip, package.client_port)
        client = MySocket()
        client.bind(client_addr)
        client.listen(1)
        while True:
            QApplication.processEvents()
            server_sock, _ = client.accept()
            server_envelope = unpack(server_sock.receive())
            server_sock.close()
            if server_envelope.get_title() == 'TaskReply':
                tasks_finished = server_envelope.get_message()['TasksFinished']
                success = server_envelope.get_message()['Success']
                error_messages = server_envelope.get_message()['ErrorMessages']
                end_of_task = server_envelope.get_message()['EndOfTasks']
                package.task_finished_number += len(tasks_finished)
                package.update_progress_bar_signal.emit()
                for task_ind, task in enumerate(tasks_finished):
                    if success[task_ind]:
                        print('Success: ' + task[0] + ' ' + task[1])
                    else:
                        print('Failed: ' + task[0] + ' ' + task[1])
                        print(error_messages[0])
                    if task[0] == 'SpikeSorting':
                        task_move_ind_list = [ind for ind, [process, data] in enumerate(package.task_wait_list) if
                                              (process == 'PostCuration') and (data == task[1])]
                        for ind in task_move_ind_list:
                            package.task_queue.append(package.task_wait_list.pop(ind))
                package.server_working = not end_of_task
            if (package.task_finished_number >= package.task_total_number) or (
                    (not package.server_working) and (not package.client_working) and (not package.task_wait_list) and
                    (not package.task_queue) and (not package.task_to_server_list)):
                if not package.thread_ending_display_flag:
                    package.thread_ending_display_flag = True
                    package.stop_timer_signal.emit()
                    for task in package.task_queue:
                        print('Failed: ' + task[0] + ' ' + task[1])
                        print('Queue abandoned because server is not responding.')
                    for task in package.task_wait_list:
                        print('Failed: ' + task[0] + ' ' + task[1])
                        print('Waiting list abandoned because server is not responding.')
                    for task in package.task_to_server_list:
                        print('Failed: ' + task[0] + ' ' + task[1])
                        print('Waiting sending to server list abandoned because server is not responding.')
                    package.task_queue = []
                    package.task_wait_list = []
                    package.task_to_server_list = []
                    time.sleep(1)
                    print('\nAll tasks finished')
                break
        client.close()
    except Exception as e:
        print(e)
        # traceback.print_exc()
        print('Error in listen_tasks_from_server thread')


def send_tasks_to_server(package, **kwargs):
    try:
        server_addr = (package.server_ip, package.port)
        while True:
            QApplication.processEvents()
            if package.task_to_server_list:
                client_sock = MySocket()
                try:
                    client_sock.connect(server_addr)
                    client_envelope = Envelope('TaskRequest',
                                               {'Tasks': package.task_to_server_list, 'UserName': package.user_name,
                                                'Parameters': {
                                                    'SpikeSorting': package.spike_sorting_parameter,
                                                    'PostCuration': package.post_curation_parameter,
                                                    'WaveformExtraction': package.waveform_extraction_parameter,
                                                    'FigureGeneration': package.figure_generation_parameter}})

                    client_sock.send(pack(client_envelope))
                    client_sock.close()
                except Exception:
                    client_sock.close()
                    print('Sending following tasks to server failed, which will be tried again after 1 mins: ')
                    pprint(package.task_to_server_list)
                    for minute in range(1 * 60):
                        if not ((package.task_finished_number >= package.task_total_number) or (
                                (not package.server_working) and (not package.client_working) and (
                        not package.task_wait_list) and
                                (not package.task_queue) and (not package.task_to_server_list))):
                            time.sleep(1)
                else:
                    package.start_timer_signal.emit()
                    package.task_to_server_list = []
                    package.server_working = True
            if (package.task_finished_number >= package.task_total_number) or (
                    (not package.server_working) and (not package.client_working) and (not package.task_wait_list) and
                    (not package.task_queue) and (not package.task_to_server_list)):
                if not package.thread_ending_display_flag:
                    package.thread_ending_display_flag = True
                    package.stop_timer_signal.emit()
                    for task in package.task_queue:
                        print('Failed: ' + task[0] + ' ' + task[1])
                        print('Queue abandoned because server is not responding.')
                    for task in package.task_wait_list:
                        print('Failed: ' + task[0] + ' ' + task[1])
                        print('Waiting list abandoned because server is not responding.')
                    for task in package.task_to_server_list:
                        print('Failed: ' + task[0] + ' ' + task[1])
                        print('Waiting sending to server list abandoned because server is not responding.')
                    package.task_queue = []
                    package.task_wait_list = []
                    package.task_to_server_list = []
                    time.sleep(1)
                    print('\nAll tasks finished')
                break
    except Exception:
        print('Error in send_tasks_to_server thread')


def do_tasks_on_client(package, **kwargs):
    try:
        while True:
            QApplication.processEvents()
            if package.task_queue:
                package.client_working = True
                post_curation_task = package.task_queue.pop(0)
                try:
                    [process, data_info] = post_curation_task
                    parameters = {'SpikeSorting': package.spike_sorting_parameter,
                                  'PostCuration': package.post_curation_parameter,
                                  'WaveformExtraction': package.waveform_extraction_parameter,
                                  'FigureGeneration': package.figure_generation_parameter}
                    failed_queue = multiprocessing.Queue()
                    if process == 'PostCuration':
                        spike_analysis_process = SpikeAnalysisProcess(post_curate_spikes, package.root, process,
                                                                      data_info, package.user_name,
                                                                      parameters, failed_queue)
                        spike_analysis_process.start()
                        package.worker_pid = spike_analysis_process.pid
                        spike_analysis_process.join()
                        package.worker_pid = None
                    else:
                        assert False, 'Process name: ' + process + ' is not PostCuration, debug!'
                    if failed_queue.empty():
                        print('Success: ' + post_curation_task[0] + ' ' + post_curation_task[1])
                    else:
                        print('Failed: ' + post_curation_task[0] + ' ' + post_curation_task[1])
                    # time.sleep(10)
                except Exception as e:
                    print('Failed: ' + post_curation_task[0] + ' ' + post_curation_task[1])
                    print(e)
                package.task_finished_number += 1
                package.update_progress_bar_signal.emit()
                task_move_ind_list = [ind for ind, [process, data] in enumerate(package.task_wait_list) if
                                      (process == 'WaveformExtraction' or process == 'FigureGeneration') and (
                                              data == post_curation_task[1])]
                for shift, ind in enumerate(task_move_ind_list):
                    package.task_to_server_list.append(package.task_wait_list.pop(ind - shift))
            else:
                package.client_working = False
            if (package.task_finished_number >= package.task_total_number) or (
                    (not package.server_working) and (not package.client_working) and (not package.task_wait_list) and
                    (not package.task_queue) and (not package.task_to_server_list)):
                if not package.thread_ending_display_flag:
                    package.thread_ending_display_flag = True
                    package.stop_timer_signal.emit()
                    for task in package.task_queue:
                        print('Failed: ' + task[0] + ' ' + task[1])
                        print('Queue abandoned because server is not responding.')
                    for task in package.task_wait_list:
                        print('Failed: ' + task[0] + ' ' + task[1])
                        print('Waiting list abandoned because server is not responding.')
                    for task in package.task_to_server_list:
                        print('Failed: ' + task[0] + ' ' + task[1])
                        print('Waiting sending to server list abandoned because server is not responding.')
                    package.task_queue = []
                    package.task_wait_list = []
                    package.task_to_server_list = []
                    time.sleep(1)
                    print('\nAll tasks finished')
                break

    except Exception as e:
        print(e)
        # traceback.print_exc()
        print('Error in do_tasks_on_client thread')