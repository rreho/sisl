#!/bin/bash

which python
which python3
which sphinx-build

if [ -n "$PYTHONUSERBASE" ]; then
  v=$(python3 -c "from sys import version_info as v ; print(f'{v[0]}.{v[1]}', end='')")
  export PYTHONPATH=$PYTHONUSERBASE/lib/python${v}/site-packages:$PYTHONPATH
fi

# No threading
export OMP_NUM_THREADS=1

if [ -z "$SISL_NUM_PROCS" ]; then
  # Ensure single-core
  export SISL_NUM_PROCS=1
fi

# Now ensure everything is ready...
make html
retval=$?

# If succeeded, we may overwrite the old
# documentation (if it exists)
if [ $retval -eq 0 ]; then
    echo "Success = $retval"
else
    echo "Failure = $retval"
fi
