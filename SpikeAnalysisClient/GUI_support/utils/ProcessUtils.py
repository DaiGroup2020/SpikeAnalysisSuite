import multiprocessing
import traceback

class SpikeAnalysisProcess(multiprocessing.Process):
    def __init__(self, fn, root, process, data_info, user_name, parameters, failed_queue):
        super().__init__()
        self.fn = fn
        self.root = root
        self.process = process
        self.data_info = data_info
        self.user_name = user_name
        self.parameters = parameters
        self.failed_queue = failed_queue

    def run(self) -> None:
        try:
            self.fn(self.root, *self.data_info.split(','), self.user_name, **self.parameters[self.process])
        except Exception as e:
            # traceback.print_exc()
            print(e)
            self.failed_queue.put(e)