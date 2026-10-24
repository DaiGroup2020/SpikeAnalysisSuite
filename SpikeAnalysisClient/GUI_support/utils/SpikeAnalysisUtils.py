import numpy as np

def task_separation(task_list, **kwargs):
    tasks = np.array(task_list)
    data_with_post_mask = np.isin(tasks[:, 1], list(tasks[tasks[:, 0] == 'PostCuration'][:, 1]))
    tasks_for_data_with_post = tasks[data_with_post_mask]
    tasks_for_data_without_post = tasks[~data_with_post_mask]
    in_post_data_with_sort_mask = np.isin(tasks_for_data_with_post[:, 1], list(tasks_for_data_with_post[tasks_for_data_with_post[:, 0] == 'SpikeSorting'][:, 1]))
    tasks_for_data_with_post_and_sort = tasks_for_data_with_post[in_post_data_with_sort_mask]
    tasks_for_data_with_post_but_sort = tasks_for_data_with_post[~in_post_data_with_sort_mask]
    tasks_to_server = np.append(tasks_for_data_with_post_and_sort[tasks_for_data_with_post_and_sort[:, 0] == 'SpikeSorting'],
                                tasks_for_data_without_post, axis=0)
    tasks_to_wait = np.append(tasks_for_data_with_post_and_sort[~(tasks_for_data_with_post_and_sort[:, 0] == 'SpikeSorting')],
                              tasks_for_data_with_post_but_sort[~(tasks_for_data_with_post_but_sort[:, 0] == 'PostCuration')], axis=0)
    tasks_to_queue = tasks_for_data_with_post_but_sort[tasks_for_data_with_post_but_sort[:, 0] == 'PostCuration']
    return [tasks_to_server.tolist(), tasks_to_wait.tolist(), tasks_to_queue.tolist()]

