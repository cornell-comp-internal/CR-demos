#!/usr/bin/python

#TODO: Remove MPI from this to make it as simple as possible for
#first version

import os
import sys

import h5py
import numpy as np
from mpi4py import MPI

#TODO: figure out how to block system calls?

H5FILE_NAME    = "perfectNumbers.h5"
H5FILE_BACKUP  = "perfectNumbers.h5.bak"
BACKUP_CMD     = "/bin/cp " + H5FILE_NAME + " " + H5FILE_BACKUP
DATASETNAME    = "DifferenceFromPerfect"
STATUSGROUP    = "status"
RANK           = 1   


MPI_CHUNK_SIZE = 100

#
# State variables
#
chunk_counter = 0

#
# MPI variables
#

comm = MPI.COMM_WORLD
info = MPI.INFO_NULL
mpi_rank = comm.Get_rank()
mpi_size = comm.Get_size()

# Tells if a given integer is a perfect number by returning the
# difference between itself and the sum of its
# divisors (excluding itself); if the diff is 0, it is perfect.
# 
# This is toy code. Odd perfect numbers are currently being searched
# for above 10^300: http://www.oddperfect.org
# Also see : http://rosettacode.org/wiki/Perfect_numbers
#          : http://en.wikipedia.org/wiki/List_of_perfect_numbers
def perfect_diff(n):
    divisor_sum = 0
    for i in range(1, n): 
        if n % i == 0:
            divisor_sum += i
    return divisor_sum - n

def broadcast_state(comm, new_evens, new_odds):
    mpi_type = MPI.__TypeDict__[new_evens.dtype.char]
    comm.Allreduce(MPI.IN_PLACE, [new_evens, mpi_type], op=MPI.SUM)
    comm.Allreduce(MPI.IN_PLACE, [new_odds,  mpi_type], op=MPI.SUM)
    return 0

def backup_file():
    os.system(BACKUP_CMD)

def checkpoint(comm, info, perf_diffs):
    dimsm  = (chunk_counter * MPI_CHUNK_SIZE,)
    dimsf  = (dimsm[0] * mpi_size,)

    start  = mpi_rank * MPI_CHUNK_SIZE
    end    = start + MPI_CHUNK_SIZE

    if mpi_rank == 0:
        if os.path.isfile(H5FILE_NAME):
            backup_file()

    file_id = h5py.File(H5FILE_NAME, "w", driver="mpio", comm=comm)
    dset_id = file_id.create_dataset(DATASETNAME, shape=dimsf, dtype='i8')
    print dset_id.shape
    print "\n"
    print "index params %d:%d:%d:%d\n" % (mpi_rank, start, end, dimsf[0])
    print str(perf_diffs)[1:-1]

    for ii in range(0, chunk_counter):
        start_ii = start + ii*mpi_size*MPI_CHUNK_SIZE
        end_ii   = start_ii + MPI_CHUNK_SIZE
        dset_id[start_ii:end_ii] = perf_diffs[ii*MPI_CHUNK_SIZE:(ii+1)*MPI_CHUNK_SIZE]
    
    file_id.close()

    if chunk_counter > 2:
        sys.exit(0)

def main(argv=None):
    if argv is None:
        argv = sys.argv

    global chunk_counter

    num_even = 0
    num_odd = 0

    #If not restored (TODO)
    counter = MPI_CHUNK_SIZE * mpi_rank
    chunk_counter += 1
    current_size = chunk_counter * MPI_CHUNK_SIZE    
    perf_diffs = np.zeros(current_size, dtype=int)
    new_evens = np.zeros(1, dtype=int)
    new_odds = np.zeros(1, dtype=int)

    while True:
        new_evens[0] = 0
        new_odds[0] = 0
        while True:
            index = MPI_CHUNK_SIZE * (chunk_counter-1) + counter % MPI_CHUNK_SIZE
            perf_diffs[index] = perfect_diff(counter) 
            if (perf_diffs[index] == 0):
                print("Found %d!\n" % counter)
                if counter % 2 == 0:
                    new_evens[0] += 1
                else:
                    new_odds[0] += 1
            perf_diffs[index] = counter # For DEBUG
            counter += 1
            if counter % MPI_CHUNK_SIZE == 0:
                break
        broadcast_state(comm, new_evens, new_odds)
        num_even += new_evens[0]
        num_odd  += new_odds[0]
        checkpoint(comm, info, perf_diffs)
        # offset into next iteration
        counter += (mpi_size - 1) * MPI_CHUNK_SIZE
        chunk_counter += 1
        current_size = chunk_counter * MPI_CHUNK_SIZE
        perf_diffs.resize(current_size)
        

if __name__ == "__main__":
    sys.exit(main())

