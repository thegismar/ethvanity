from web3 import Web3
from tqdm import tqdm
import multiprocessing as mp
from rich import pretty
from rich.console import Console
from dotenv import load_dotenv
import os


load_dotenv()
CHARS = os.getenv('CHARS')
THREADS = int(os.getenv('THREADS'))
pretty.install()
console = Console()
LEN = len( CHARS )


class Vanity( Web3 ):

    def __init__(self):
        super().__init__()
        self.eth.account.enable_unaudited_hdwallet_features()
        self.vanity = None

    def __next__(self):
        self.vanity = self.eth.account.create_with_mnemonic()

    def __iter__(self):
        return self


def listener(q):
    t = tqdm()
    for item in iter( q.get, None ):
        t.update()


def loop(q, event):
    v = Vanity()
    while not event.is_set():
        next( v )
        if str( v.vanity[0].address[0:LEN] ).lower() == CHARS:
            with open( 'key', 'a' ) as f:
                txt = f'address: {v.vanity[0].address}, mnemonic: {v.vanity[1]}'
                f.write( txt + '\n')
            event.set()
            console.log(f'[bold green]Found wallet: {txt}')
            return
        q.put( 1 )

    return


if __name__ == '__main__':
    console.clear(home=True)
    q = mp.Queue()
    proc = mp.Process( target=listener, args=(q,) )
    proc.start()

    event = mp.Event()
    workers = [mp.Process( target=loop, args=(q, event,) ) for i in range( THREADS )]

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()

    q.put( None )
    proc.join()
