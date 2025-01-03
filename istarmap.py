#!/usr/bin/env python3
# 
# istarmap.py
# 
# Created by Nicolas Fricker on 06/23/2024.
# Copyright © 2024 Nicolas Fricker. All rights reserved.
# 

# istarmap.py for Python 3.8+
import tqdm
import multiprocessing.pool as mpp
from threading import Thread
from multiprocessing import Manager

def istarmap(self, func, iterable, chunksize=1):
	"""starmap-version of imap"""
	self._check_running()
	if chunksize < 1:
		raise ValueError(
			"Chunksize must be 1+, not {0:n}".format(chunksize)
		)

	task_batches = mpp.Pool._get_tasks(func, iterable, chunksize)
	result = mpp.IMapIterator(self)
	self._taskqueue.put(
		(
			self._guarded_task_generation(
				result._job,
				mpp.starmapstar,
				task_batches
			),
			result._set_length
		)
	)
	return (item for chunk in result for item in chunk)

mpp.Pool.istarmap = istarmap

def istarmap_tqdm(self, func, iterable, chunksize=1):
	"""starmap-version of imap"""
	self._check_running()
	if chunksize < 1:
		raise ValueError(
			"Chunksize must be 1+, not {0:n}".format(chunksize)
		)
	
	num_processes = self._processes
	manager = Manager()
	queue = manager.Queue()

	pbars = [
		tqdm.tqdm(total=0, position=i+1)
		for i in range(num_processes)
	]

	def _progress_updater():
		active_processes = num_processes
		while active_processes > 0:
			update = queue.get()
			if update is None:
				active_processes -= 1
				continue
			if len(update) != 2:
				continue
			idx, update = update
			pbar = pbars[idx]
			if isinstance(update, dict):
				for k, v in update.items():
					setattr(pbar, k, v)
			elif isinstance(update, int):
				pbar.update(update)
		for pbar in pbars:
			pbar.close()

	listener = Thread(target=_progress_updater, daemon=True)
	listener.start()

	task_batches = mpp.Pool._get_tasks(
		func,
		((queue, *([arg] if not isinstance(arg, (tuple, list)) else arg)) for arg in iterable),
		chunksize
	)
	result = mpp.IMapIterator(self)
	self._taskqueue.put(
		(
			self._guarded_task_generation(
				result._job,
				mpp.starmapstar,
				task_batches
			),
			result._set_length
		)
	)

	def result_generator():
		try:
			for chunk in result:
				for item in chunk:
					yield item
		finally:
			for _ in range(num_processes):
				queue.put(None)

			listener.join()

	return result_generator()

mpp.Pool.istarmap_tqdm = istarmap_tqdm
