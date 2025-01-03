# istarmap_tqdm
multiprocessing Pool istarmap with tqdm per process integration

```python3
import time
import random
import multiprocessing as mp

# import istarmap after multiprocessing
import istarmap

def _process_worker(queue, indexes):
	# current Process index
	idx = mp.current_process()._identity[0]-1
	counter = 0
	indexes = list(indexes)
	# update tqd.tqdm attributes
	queue.put((idx, {'total': len(indexes), 'desc': f"Process: {idx}", 'leave': False}))
	for i in indexes:
		time.sleep(random.randint(1, 10) / 10)
		counter += i
		# update current Process tqdm.tqdm progress bar by 1
		queue.put((idx, 1))
	return counter

if __name__ == "__main__":
	with tqdm.tqdm(desc='Main', total=4, position=0) as pbar:
		with mp.Pool(processes=4) as pool:
			args = ((range(10),) for _ in range(4))
			for i in pool.istarmap_tqdm(_process_worker, args, chunksize=1):
				pbar.update(1)
				pbar.refresh()

```
