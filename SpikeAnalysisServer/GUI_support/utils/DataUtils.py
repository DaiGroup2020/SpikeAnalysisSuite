class TaskReplyBuffer(object):
    def __init__(self):
        self.task_finished_list = []
        self.success_list = []
        self.error_message_list = []

    def get_reply(self):
        return [self.task_finished_list, self.success_list, self.error_message_list]

    def put_reply(self, task_finished, success, error_message):
        self.task_finished_list.append(task_finished)
        self.success_list.append(success)
        self.error_message_list.append(error_message)

    def clear(self):
        self.task_finished_list = []
        self.success_list = []
        self.error_message_list = []