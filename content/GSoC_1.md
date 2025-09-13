title: GSoC_summary 
date: September 9, 2025
author: Hengye Zhu
category: GSoC

This project will convert Macaque auditory thalamocortical circuits model based on NetPyNE implementation into NeuroML standard formats and testing it across multiple simulation engines to ensure that it produce the same results.

First, I converted the morphology and ion channels for almost all neurons in the Macaque_auditory_thalamocortical_model. The conversions for IT2 and RE neurons have been confirmed to be correct, but there are unknown errors when integrating them.

:) specific issue can be found at:
 https://github.com/OpenSourceBrain/Macaque_auditory_thalamocortical_model_data/issues/14 

:) The community can access model's information here: https://github.com/OpenSourceBrain/Macaque_auditory_thalamocortical_model_data/tree/feat-neuroml-gsoc/NeuroML2.

Then, I also added functionality to directly import nml files to the existing script, and introduced some new features for recording simulation variables, which can be used for subsequent validation. My script might not be written in the elegant way, but it may help beginners understand NeuroML better.

Please refer to:
https://github.com/OpenSourceBrain/Macaque_auditory_thalamocortical_model_data/blob/feat-neuroml-gsoc/NeuroML2/compare_MC/RE/omv_test.py

Finally, this GSoC project is still ongoing, and I look forward to the journey ahead! Here, I would like to express my gratitude to my mentors: Ankur Sinha and Padraig Gleeson.