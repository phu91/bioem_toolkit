# move to the folder where you have all the pdbs.
#TODO, make this part of the existing bioem pipeline. 

for mod in $(ls *pdb);  do awk '$1=="ATOM" && $NF!="H"' ${mod} | awk '{if(NF==12){ne=0;if($12=="N")ne=7;if($12=="C")ne=6;if($12=="O")ne=8;if($12=="S")ne=16;if($12=="P")ne=15; printf "%f %f %f %f %f\n",$7,$8,$9,1.3,ne}}' >  ${mod}.txt; done

