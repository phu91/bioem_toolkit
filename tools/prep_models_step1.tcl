set start 0

mol new MODEL0.PDB
mol addfile trajectory.crd first $start last -1 step 20 waitfor all

set nframe [molinfo top get numframes]	 

for {set i 1} {$i <= $nframe} {incr i} {
	set all [atomselect top all frame $i]
	$all writepdb [format "md_%02d.pdb" $i]
}

exit

