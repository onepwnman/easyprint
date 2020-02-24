#!/bin/bash

# Support file type: STL

"${BASEDIR}"/util/CuraEngine/build/CuraEngine slice -v -j "${BASEDIR}"/settings/printer/anet_a8.def.json -s ${3} -s ${4} -l ${1} -o ${2} 2>parse.log
header_start_in_log=`expr $(grep -n "Gcode header after slicing:"  parse.log | cut -d":" -f1) + 1`
header_end_in_log=`expr $(grep -n "End of gcode header."           parse.log | cut -d":" -f1) - 1`
header_end_in_gcode=$(grep -n ";Generated with Cura_SteamEngine master" ${2} | cut -d":" -f1)

sed -n "${header_start_in_log},${header_end_in_log}p" parse.log > gcode_tmp
sed -n "${header_end_in_gcode},$ p" ${2} >> gcode_tmp 
mv gcode_tmp ${2}
rm parse.log


