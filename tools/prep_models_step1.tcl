set start 0
set end 20 

mol new MODEL0.PDB
mol addfile trajectory.crd first $start last $end waitfor all

for {set i 1} {$i <= $end} {incr i} {
	set all [atomselect top all]
	$all writepdb model_$i.pdb
}

exit

