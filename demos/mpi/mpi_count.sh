#!/bin/csh

#SBATCH -J myMPI          # Job Name
#SBATCH -o myMPI.o%j      # Name of the output file (myMPI.oJobID)
#SBATCH -p development    # Queue name
#SBATCH -t 00:05:00       # Run time (hh:mm:ss) - 5 minutes
#SBATCH -N 1              # Requests 1 MPI node
#SBATCH -n 4              # 16 tasks total
#SBATCH -e myMPI.err%j    # Direct error to the error file
#SBATCH -A TG-STA110019S  # Account number (replace with yours)

ibrun mpi_count
