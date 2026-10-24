import multiprocessing
import traceback

class SpikeAnalysisProcess(multiprocessing.Process):
    def __init__(self, fn, root, process, data_info, parameters, result_queue):
        super().__init__()
        self.fn = fn
        self.root = root
        self.process = process
        self.data_info = data_info
        self.parameters = parameters
        self.result_queue = result_queue

    def run(self) -> None:
        try:
            self.fn(self.root, *self.data_info.split(','), **self.parameters[self.process])
            self.result_queue.put('Success')
        except Exception as e:
            # traceback.print_exc()
            # print(e)
            self.result_queue.put(str(e))