from fabric.api import *
import time
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


env.servers = ['user@<server1>:22',
               'user@<server2>:22',
               'user@<server2>:22']
env.roledefs['servers'] = env.servers


@task
@parallel
@roles('servers')
def install():
    sudo("apt-get update")
    sudo("apt-get install dstat dtach")


@task
def runExp():
    execute(experiment, hosts=env.servers)
    process()


@parallel
def experiment():
    run(dtach_and_log("dstat --output dstat.log 1 8", "tmp.log", "/dev/null"))
    with settings(warn_only=True):
        run('rm dstat.log')
        run('seq 3 | xargs -P0 -n1 timeout 5 md5sum /dev/zero')
    time.sleep(8)
    get("dstat.log", "logs/%(host)s")


def dtach_and_log(command, dtach_socket, logfile):
    """Generate a command to leave the program running in the background
    with its output copied to a logfile.
    source: https://github.com/pacheco/GlobalFS/blob/master/src/scripts/fabfile-exp.py
    """
    return 'dtach -n %s bash -c "%s | tee %s"' % (dtach_socket, command, logfile)


def process():
    processed = pd.DataFrame()
    plt.figure()
    for i, logfile in enumerate(env.servers):
        df = pd.read_csv('logs/' + logfile, index_col=False, header=1, skiprows=5)
        processed['server ' + str(i)] = 100 - df['idl']
        processed.plot()
        plt.xlabel('time [s]')
        plt.ylabel('CPU load [%]')
        plt.grid(color='gray', linestyle='dashed')
    plt.savefig('imgs/load.png')
    processed.to_csv('processed.csv')