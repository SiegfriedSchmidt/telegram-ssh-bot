import asyncio


class AsyncioWorkers:
    def __init__(self, rate=3):
        self.queue = asyncio.Queue()
        self.rate = rate
        self.workers = []

    def start(self, num_workers=1):
        if self.workers:
            raise Exception('Workers already started!')
        self.workers = [asyncio.create_task(self.__worker(i)) for i in range(num_workers)]

    async def __worker(self, worker_id: int):
        while True:
            future, func, args, kwargs = await self.queue.get()
            try:
                future.set_result(await func(*args, **kwargs))
            except Exception as e:
                future.set_exception(e)
            finally:
                self.queue.task_done()

            await asyncio.sleep(self.rate)

    async def enqueue_task(self, func, *args, **kwargs):
        """
        Enqueue a task and return an awaitable future that will hold the result.
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        await self.queue.put((future, func, args, kwargs))
        return await future

    async def shutdown(self):
        # Cancel all worker tasks gracefully
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)


if __name__ == '__main__':
    asyncio_workers_test = AsyncioWorkers()


    async def main():
        asyncio_workers_test.start(num_workers=1)

        async def sample_task(x):
            await asyncio.sleep(1)
            return x * 2

        result1 = asyncio_workers_test.enqueue_task(sample_task, 10)
        result2 = asyncio_workers_test.enqueue_task(sample_task, 20)
        print("Result1:", await result1)
        print("Result2:", await result2)


    asyncio.run(main())
