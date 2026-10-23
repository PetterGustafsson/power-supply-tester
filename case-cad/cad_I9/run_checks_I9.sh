#!/bin/sh
# I9 post-build chain (nohup): 3MF, mesh clearances, rib clearances, wall check, review views, validation, sheet
P=../.venv/bin/python
$P -u make_3mf.py > m3.log 2>&1; echo "3mf $?" > chain.log
$P -u clear_I7.py > clear.log 2>&1; echo "clear $?" >> chain.log
$P -u ribs_check_I9.py > ribs_check.log 2>&1; echo "ribs $?" >> chain.log
$P -u wall_check_I9.py > wall.log 2>&1; echo "wall $?" >> chain.log
$P -u views.py > views.log 2>&1; echo "views $?" >> chain.log
$P -u validate.py > val.log 2>&1; echo "validate $?" >> chain.log
$P -u sheet.py > sheet.log 2>&1; echo "sheet $?" >> chain.log
