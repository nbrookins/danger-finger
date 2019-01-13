#!/bin/sh
echo " "
echo "3d Print finger script, Nick Brookins (c) 2015"
echo "Usage: render.sh [build_item (1-10)]"
echo "Build items: [0:All, 1:Frame, 2:Flexible, 3:Base, 4:Middle, 5:Tip, 6:Tip Cover, 7:Bumper, 8:Socket, 9:Hinge Plugs, 10:Linkage]"
echo " "
echo " "
l=$'\n'

items[1]="Plastic"
items[2]="Flexible"
items[3]="Base"
items[4]="Middle"
items[5]="Tip"
items[6]="TipCover"
items[7]="Bumper"
items[8]="Socket"
items[9]="HingePlugs"
items[10]="Linkage"
items[11]="Clamp"

scadfilename="danger-finger.scad"

num="$1"
if [ "$num" == "" ] ; then
	num="$(seq 3 11)"
fi
if [ "$num" == "-1" ] ; then
	num="$(seq 3 11)"
fi
if [ "$num" == "1" ] ; then
	num="$(seq 3 5)${l}11"
fi
if [ "$num" == "2" ] ; then
	num="$(seq 6 9)"
fi
stlpath="$(pwd)/stl_$(date +%s)"
mkdir -p $stlpath

echo "OpenScad source: $scadfilename"
echo "Generating STL to $stlpath"

PIDS=""
STARTTIME=$(date +%s)

#for i in $num; do
#    name=${items[$i]}
#    stl="$i-$name-$scadfilename.stl"
#    echo "Generating preview of $name"
#    /Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD -D 'print=1' -D 'preview=0' -D 'fast=0' -D 'rotatetest=0' -D "part=$i" --preview -o $stlpath/$stl.png $scadfilename
    #open pngpath
#done
#echo "Previews complete, beginning renders"

for i in $num; do
    name=${items[$i]}
    stl="$i-$name-$scadfilename.stl"
    /Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD -D 'print=1' -D 'preview=0' -D 'fast=0' -D 'rotatetest=0' -D "make_cutaway=0" -D "part=$i" --render -o $stlpath/$stl $scadfilename &
    PID=$!
    echo "Rendering object $i: $name, PID $PID"
    PIDS="$PIDS$l$PID"
done

for p in $PIDS; do
while kill -0 $p > /dev/null 2>&1; do
    #echo "Process $p is still active..."
    echo ".\c"
    sleep 10
done
done

ENDTIME=$(date +%s)
echo "Rendered in $(($ENDTIME - $STARTTIME)) seconds."
