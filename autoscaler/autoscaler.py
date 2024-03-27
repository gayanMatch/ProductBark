import os
import redis
import time
import logging
import threading
from commands import Commands
GPU_NUM_THRESHOLD = int(os.getenv('GPU_NUM_THRESHOLD', '2'))
GPU_TIME_THRESHOLD = int(os.getenv('GPU_TIME_THRESHOLD', '60'))
FLY_TOKEN = os.getenv('FLY_TOKEN')
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


class Monitor(threading.Thread):
    def __init__(self, redis_con):
        super().__init__()
        self.commands = Commands()
        self.redis_con = redis_con
        self.redis_con.set('stop_marked_gpu', '')
        self.num_gpu_log = []

    def run(self) -> None:
        i = 0
        num_gpu_machines = 0
        while True:
            if i == 0:
                gpu_machines = self.commands.get_machines_by_state(a='optimizedbark', state='started')
                num_gpu_machines = len(gpu_machines.strip().split('\n'))
            if i >= 600:  # every 10 minutes
                i = 0
            num_requests = int(self.redis_con.get('active_requests').decode('utf-8'))
            num_gpus = 3 * num_gpu_machines - num_requests
            self.num_gpu_log.append(num_gpus >= (GPU_NUM_THRESHOLD + 3))
            if len(self.num_gpu_log) > GPU_TIME_THRESHOLD:
                self.num_gpu_log.pop(0)
                if all(self.num_gpu_log):
                    gpu_list = []
                    _, keys = self.redis_con.scan(match='migs_*')
                    for key in keys:
                        val = self.redis_con.get(key.decode('utf-8'))
                        gpu_list.append((val, key.decode('utf-8')))
                    gpu_list.sort()
                    max_val, max_key = gpu_list[0]
                    if max_val == 3:
                        self.commands.stop_machine(a='optimizedbark', machine_id=max_key[5:])
                        logging.info(f"Stopping machine {max_key[5:]}")
                        num_gpu_machines -= 1
                        self.redis_con.set('stop_marked_gpu', '')
                        self.redis_con.set(max_key, 0)
                    else:
                        self.redis_con.set('stop_marked_gpu', max_key[5:])
            if num_gpus < GPU_NUM_THRESHOLD:
                # scale up
                self.commands.start(a='optimizedbark', count=1)
                logging.info(f"Starting machine")
                num_gpu_machines += 1
            # self.redis_con.lpush('available_gpus', json.dumps({'time': time.time(), 'num_gpus': num_gpus}))
            time.sleep(1)
            i += 1


if __name__ == '__main__':
    redis_url = os.environ.get("redis_url",
                               'redis://default:eb7199cbf0f54bf5bb084f7f1d594692@fly-bark-queries.upstash.io:6379')
    r = redis.Redis.from_url(redis_url)
    monitor = Monitor(r)
    monitor.start()
    monitor.join()
