title: Report 1
date: June 12, 2025
author: Hengye Zhu
category: GSoC

I will temporarily record my work progress and issues here.

First, I attempted to directly convert from NetPyNE to NeuroML2 using its built-in function, as shown below:
```python
sim.createExportNeuroML2(netParams = netParams, simConfig = simConfig,reference = '')
```
However, several issues arose, such as certain complex ionic currents failing to be parsed, and segment connections being restricted to positions 0 and 1 (unable to handle intermediate positions like 0.5).

Based on the observed limitations, this built-in function appears to be restricted to morphology data export.

Next, I attempted to instantiate the JSON file using NetPyNE, but encountered issues with recording voltage traces. Currently, this is still under investigation.

To be done...
