from multiprocessing import Pool, cpu_count
from node import settings

pool = Pool(getattr(settings, 'WORKER_COUNT', cpu_count()))
__all__ = ('pool',)