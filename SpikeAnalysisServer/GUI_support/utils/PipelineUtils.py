import traceback

from .NetworkUtils import pack, unpack, Envelope, MySocket
from .ThreadUtils import ServerThread
from .DataUtils import TaskReplyBuffer
from .FunctionUtils import kill_process_tree
import multiprocessing
from .ProcessUtils import SpikeAnalysisProcess
from .SpikeAnalysisCore.module_bank import sort_spikes, waveform_extraction_after_phy, \
    single_recording_figure_generation, clear_cache

def server_main_thread(package):
    server_addr = (package.server_ip, package.port)
    server = MySocket()
    server.bind(server_addr)
    server.listen(10)
    while True:
        client_sock, client_addr = server.accept()
        if package.run_stop_set.is_set():
            client_sock.close()
            break
        thread_sub = ServerThread(server_sub_thread, package, client_sock, client_addr)
        thread_sub.start()
    server.close()


def server_sub_thread(package, client_sock, client_addr):
    client_envelope = unpack(client_sock.receive())
    client_envelope_title = client_envelope.get_title()
    if client_envelope_title == 'LoginRequest':
        user_name = client_envelope.get_message()['UserName']
        password = client_envelope.get_message()['Password']
        if user_name not in package.user_info.keys():
            validate = 'UserNotFound'
            user_name_folder = None
        elif not package.user_info[user_name]['Password'] == password:
            validate = 'Unmatch'
            user_name_folder = None
        else:
            print('User: '+user_name+' log in.')
            validate = 'Success'
            user_name_folder = package.user_info[user_name]['Folder']
        server_envelope = Envelope('LoginReply', {'Validate': validate, 'UserFolderName': user_name_folder})
        server_sock = MySocket()
        server_sock.connect((client_addr[0], package.client_port))
        server_sock.send(pack(server_envelope))
        server_sock.close()
    elif client_envelope_title == 'TaskRequest':
        user_name = client_envelope.get_message()['UserName']
        tasks = client_envelope.get_message()['Tasks']
        parameters = client_envelope.get_message()['Parameters']
        package.client_ip_dict[user_name] = client_addr[0]
        if user_name not in package.process_data_parameter_queue_dict.keys():
            package.process_data_parameter_queue_dict[user_name] = []
        for task in tasks:
            package.process_data_parameter_queue_dict[user_name].append([task[0], task[1], parameters])
        if user_name not in package.task_reply_buffer_dict.keys():
            package.task_reply_buffer_dict[user_name] = TaskReplyBuffer()
        if user_name not in package.current_user_list:
            package.current_user_list.append(user_name)
            do_task_worker = ServerThread(do_tasks_on_client, package, user_name)
            do_task_worker.start()
    elif client_envelope_title == 'TerminationRequest':
        user_name = client_envelope.get_message()['UserName']
        if user_name in package.process_data_parameter_queue_dict.keys():
            package.process_data_parameter_queue_dict[user_name] = []
        if user_name in package.pid_dict.keys():
            kill_process_tree(package.pid_dict[user_name])
    else:
        print('Message with unknown title: ' + client_envelope_title + ' received, debug!')


def do_tasks_on_client(package, user_name):
    try:
        while True:
            if package.process_data_parameter_queue_dict[user_name]:
                process_data_parameter = package.process_data_parameter_queue_dict[user_name].pop(0)
                try:
                    [process, data_info, parameters] = process_data_parameter
                    result_queue = multiprocessing.Queue()
                    if process == 'SpikeSorting':
                        spike_analysis_process = SpikeAnalysisProcess(sort_spikes, package.root, process, data_info,
                                                                      parameters, result_queue)
                        spike_analysis_process.start()
                        package.pid_dict[user_name] = spike_analysis_process.pid
                        package.task_manager_update_signal.emit([user_name, package.client_ip_dict[user_name],
                                                                 package.pid_dict[user_name], process, data_info])
                        spike_analysis_process.join()
                        try:
                            clear_cache(*data_info.split(','))
                        except Exception as e:
                            print(e)
                        del package.pid_dict[user_name]
                    elif process == 'WaveformExtraction':
                        spike_analysis_process = SpikeAnalysisProcess(waveform_extraction_after_phy, package.root,
                                                                      process, data_info,
                                                                      parameters, result_queue)
                        spike_analysis_process.start()
                        package.pid_dict[user_name] = spike_analysis_process.pid
                        package.task_manager_update_signal.emit([user_name, package.client_ip_dict[user_name],
                                                                 package.pid_dict[user_name], process, data_info])
                        spike_analysis_process.join()
                        try:
                            clear_cache(*data_info.split(','))
                        except Exception as e:
                            print(e)
                        del package.pid_dict[user_name]
                    elif process == 'FigureGeneration':
                        spike_analysis_process = SpikeAnalysisProcess(single_recording_figure_generation, package.root,
                                                                      process, data_info,
                                                                      parameters, result_queue)
                        spike_analysis_process.start()
                        package.pid_dict[user_name] = spike_analysis_process.pid
                        package.task_manager_update_signal.emit([user_name, package.client_ip_dict[user_name],
                                                                 package.pid_dict[user_name], process, data_info])
                        spike_analysis_process.join()
                        try:
                            clear_cache(*data_info.split(','))
                        except Exception as e:
                            print(e)
                        del package.pid_dict[user_name]
                    else:
                        assert False, 'Process name: ' + process + ' is not in [SpikeSorting, WaveformExtraction, FigureGeneration], debug!'
                    task_finished = [process_data_parameter[0], process_data_parameter[1]]
                    if result_queue.empty():
                        success = False
                        error_message = 'Process half terminated'
                        print('User ' + user_name + ' failed: ', process_data_parameter[0],
                              process_data_parameter[1])
                        print(error_message)
                    else:
                        result_message = result_queue.get()
                        if result_message == 'Success':
                            success = True
                            error_message = ''
                            print('User ' + user_name + ' success: ', process_data_parameter[0],
                                  process_data_parameter[1])
                        else:
                            success = False
                            error_message = result_message
                            print('User ' + user_name + ' failed: ', process_data_parameter[0],
                                  process_data_parameter[1])
                            print(error_message)
                except Exception as e:
                    print('User ' + user_name + ' failed: ', process_data_parameter[0], process_data_parameter[1])
                    print(e)
                    task_finished = [process_data_parameter[0], process_data_parameter[1]]
                    success = False
                    error_message = str(e)
                package.task_reply_buffer_dict[user_name].put_reply(task_finished, success, error_message)
                if package.process_data_parameter_queue_dict[user_name]:
                    end_of_tasks = False
                else:
                    end_of_tasks = True
                server_sock = MySocket()
                try:
                    server_sock.connect((package.client_ip_dict[user_name], package.client_port))
                    task_reply_message = package.task_reply_buffer_dict[user_name].get_reply()
                    server_envelope = Envelope('TaskReply', {'TasksFinished': task_reply_message[0],
                                                             'Success': task_reply_message[1],
                                                             'ErrorMessages': task_reply_message[2],
                                                             'EndOfTasks': end_of_tasks})
                    server_sock.send(pack(server_envelope))
                    server_sock.close()
                except Exception:
                    server_sock.close()
                    print('Sending task replies to ' + user_name + ' client failed, which will be tried next time. ')
                else:
                    package.task_reply_buffer_dict[user_name].clear()
            else:
                break
        if user_name in package.process_data_parameter_queue_dict.keys():
            del package.process_data_parameter_queue_dict[user_name]
        if user_name in package.client_ip_dict.keys():
            del package.client_ip_dict[user_name]
        if user_name in package.task_reply_buffer_dict.keys():
            del package.task_reply_buffer_dict[user_name]
        if user_name in package.current_user_list:
            package.current_user_list.remove(user_name)
        print('User: ' + user_name + ' thread finished.')
    except Exception as e:
        traceback.print_exc()
        print(e)
        print('Worker for ' + user_name + ' failed.')
    finally:
        package.task_manager_clear_signal.emit(user_name)