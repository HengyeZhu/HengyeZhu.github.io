title: json2nml_Scripts 
date: June 1, 2025
author: Hengye Zhu
category: GSoC

Hello everyone! Today I'd like to share several scripts I developed during GSoC for converting morphological data from JSON format to NeuroML format.  

### Step 1: JSON to HOC Conversion

First, we'll extract the morphological data and convert it to HOC format:

```python
import json

### extract morphology data and then make manual adjustments
with open('L1_HAC_cIR216_1_cellParams.json') as file:
    data = json.load(file)

topol_data = {}
for sec_name, sec_info in data['secs'].items():
    if 'topol' in sec_info:
        topol_data[sec_name] = sec_info['topol']

morpho_data = {}
for sec_name, sec_info in data['secs'].items():
    if 'geom' in sec_info and 'pt3d' in sec_info['geom']:
        morpho_data[sec_name] = sec_info['geom']['pt3d']

connections = []
sections = {}

for sec_name, topol_info in topol_data.items():
    parent_sec = topol_info.get('parentSec')
    if parent_sec:
        connections.append((sec_name.strip(), parent_sec))

for sec_name, pt3d_info in morpho_data.items():
    sections[sec_name] = []
    for point in pt3d_info:
        sections[sec_name].append(point)

hoc_code = ""

hoc_code += "proc topol() { \n"
for child, parent in connections:
    hoc_code += f"  connect {child}(0), {parent}(1)\n"
hoc_code += "}\n\n"

for sec_name, pt3d_points in sections.items():
    hoc_code += f"  {sec_name} {{\n"  
    hoc_code += "    pt3dclear()\n"
    for point in pt3d_points:
        x, y, z, diam = point
        hoc_code += f"    pt3dadd({x}, {y}, {z}, {diam})\n"  
    hoc_code += "  }\n"  

with open('L1_HAC_cIR216_1_cell.hoc', 'w') as file:
    file.write(hoc_code)
```



### Step 2: Manual HOC Completion → NML Export

Then, we can manually complete the HOC file and use NeuroML's built-in functions:

```python
#!/usr/bin/env python3
"""
Convert cell morphology to NeuroML.

We only export morphologies here. We add the biophysics manually.

File: NeuroML2/scripts/cell2nml.py
"""

import os
import sys

import pyneuroml
from pyneuroml.neuron import export_to_neuroml2
from neuron import h


def main(acell):
    """Main runner method.

    :param acell: name of cell
    :returns: None

    """
    loader_hoc_file = f"{acell}_loader.hoc"
    loader_hoc_file_txt = """
    /*load_file("nrngui.hoc")*/
    load_file("stdrun.hoc")
    xopen("your_path/L1_HAC_cIR216_1_cell.hoc")
    objref cell
    cell = new L1_HAC_cIR216_1_cell()
    """

    with open(loader_hoc_file, 'w') as f:
        print(loader_hoc_file_txt, file=f)

    export_to_neuroml2(loader_hoc_file, f"{acell}.nml",
                       includeBiophysicalProperties=False, validate=False)

    os.remove(loader_hoc_file)
    # Note--a couple of diameters are 0.0, modified to 0.001 to validate the
    # model


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("This script only accepts one argument.")
        sys.exit(1)
    main(sys.argv[1])
```

### Step 3: Handling nseg Data

Next, we'll extract the nseg count and write it into the NML file:

```python
import json

file_name = 'L1_DLAC_cNAC187_1_cellParams.json'
with open(file_name, 'r') as file:
    data = json.load(file)

section_nseg_mapping = []

if 'secs' in data:
    for section, properties in data['secs'].items():
        nseg = properties['geom']['nseg']
        section_nseg_mapping.append((section, nseg))

output_file_name = 'section_nseg_mapping.txt'
with open(output_file_name, 'w') as output_file:
    for section, nseg in section_nseg_mapping:
        output_file.write(f"{section}: {nseg}\n")

print("Section and nseg mapping:")
for section, nseg in section_nseg_mapping:
    print(f"{section}: {nseg}")

print(f"\nResults have been saved to {output_file_name}")
```
And

```python
import xml.etree.ElementTree as ET

NAMESPACE = "http://www.neuroml.org/schema/neuroml2"

nseg_mapping = {}
with open("section_nseg_mapping.txt", "r") as file:
    for line in file:
        section, nseg = line.strip().split(": ")
        nseg_mapping[section] = nseg

nml_file = "L1_DLAC_cNAC187_1_cell.morph.cell.nml" 
tree = ET.parse(nml_file)
root = tree.getroot()

for segment_group in root.findall(".//{{{}}}segmentGroup".format(NAMESPACE)):
    group_id = segment_group.get("id")
    if group_id in nseg_mapping:
        prop = ET.Element("{{{}}}property".format(NAMESPACE), tag="numberInternalDivisions", value=nseg_mapping[group_id])
        segment_group.insert(0, prop)  

ET.register_namespace("", NAMESPACE)
tree.write("L1_DLAC_cNAC187_1_cell.morph.cell.nml", encoding="UTF-8", xml_declaration=True)
```

If time permits, I'll continue improving these scripts—one potential enhancement would be eliminating the manual completion of HOC files by directly converting the extracted JSON data into a HOC template.  

Thanks for reading!

