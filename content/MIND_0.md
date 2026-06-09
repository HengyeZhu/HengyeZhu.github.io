title: MIND Simulator Demo
date: June 9, 2026
author: Hengye Zhu
category: MIND

This post presents a [**MIND_Sim**](https://github.com/HengyeZhu/MIND_Sim) demo. The demo couples a detailed hippocampal CA3 microcircuit to a whole-brain neural mass model and illustrates the basic workflow of MIND_Sim.

The demo uses a synthetic connectivity matrix. Users who want to reproduce the subject-specific workflow can download the HCP `100206` data and run the preprocessing script provided by MIND_Sim [here](https://github.com/HengyeZhu/MIND_Sim/blob/main/examples/ca3_epilepsy_cosim/mind_sim/prepare_hcp100206_ca3.py).

The complete workflow is implemented [here](https://github.com/HengyeZhu/MIND_Sim/blob/main/examples/ca3_epilepsy_cosim/mind_sim/run_vep_ca3_cosim.py).

## Data Overview

The micro model is based on the CA3 epilepsy network from [ModelDB 186768](https://modeldb.science/showmodel?model=186768). The CA3 microcircuit is represented by pyramidal cells, basket cells, and OLM interneurons with simplified morphologies.

The macro model is based on the [TVB `Epileptor2D` neural mass model](https://docs.thevirtualbrain.org/api/tvb.simulator.models.html#tvb.simulator.models.epileptor.Epileptor2D). It represents whole-brain regional dynamics on top of the connectivity matrix, while the CA3 region can be replaced by the detailed microcircuit.

The model mechanisms are organized under one directory:

```text
ca3_epilepsy_cosim/mind_sim/mod/
```

The `mod/` directory contains both the standard NEURON/CoreNEURON mechanisms for the CA3 microcircuit and the MIND_Sim extended MOD modules for macro dynamics, `macro2macro coupling`, `micro2macro transforms`, and `macro2micro transforms`.

Since the main goal of this demo is to demonstrate the MIND_Sim workflow, the model parameters were not specifically optimized; instead, they largely follow the original model settings.

## Simulation Setup

Before running the script, compile the MOD mechanisms from the example directory:

```bash
cd ca3_epilepsy_cosim/mind_sim
mind_nrnivmodl mod
```

After compilation, the setup step loads the required mechanisms and sets the basic simulation resolution.

```py
from pathlib import Path
import mind_sim as ms

ms.macro.load_mech(Path(__file__).resolve().parent / "mod")
ms.macro.dt(0.1)
ms.macro.exchange_window(0.5)

micro = ms.Sim()
micro.set_device("cpu")
micro.set_num_threads(int(args.micro_threads))
micro.set_dt(0.025)
micro.load_mech(str(Path(__file__).resolve().parent / "mod"))
```

Here, `micro.set_device("cpu")` selects CPU execution for the micro simulator, and `micro.set_num_threads(...)` configures CPU threads. The macro part of MIND_Sim is single-threaded and forms a pipeline with the micro simulation, while the micro part is backed by CoreNEURON and supports CPU multithreading and GPU execution.

## Load ROIs

The first step in MIND_Sim is to create ROIs from a connectivity matrix like [this](https://github.com/HengyeZhu/MIND_Sim/blob/main/examples/ca3_epilepsy_cosim/data/synthetic_hybrid_ca3_connectivity.csv).

```py
import mind_sim as ms

rois = ms.macro.load_rois(args.connectivity_csv)
left_ca3_roi = rois.roi("Left-CA3")
```

Here, `load_rois` reads the connectivity matrix and creates one ROI object for each region label. The returned ROI collection stores the region labels, connection weights, and delays, and individual ROIs can be accessed by name.

## Micro Modeling

MIND_Sim is inspired by [NeuroML](https://neuroml.org/): neurons with the same morphology are treated as instances of one template. This is one source of frontend construction speedup, and it is also a modeling semantic that users should follow when defining populations.

To use a morphology template, users can load an SWC file and modify the generated sections, or build sections from scratch as shown below. The API is `ms.section(name, label)`, where `label` is the section group name. Users then call `micro.build_morphology(...)` explicitly and pass the sections used by each population. This differs from standard NEURON scripting: MIND_Sim does not instantiate every cell immediately when Python statements are executed. Instead, the Python frontend records model-building operations, and the corresponding C++ structures are constructed in batch. Later, `micro.build_microcircuit()` builds the biophysical properties and network connectivity after mechanisms, synapses, and connections have been specified.

MIND_Sim allows mechanisms to be inserted at several granularities, including the whole cell, a section group, a single section, or a specific section location.

```py
pyr_soma = ms.section("soma", "soma")
pyr_soma.nseg = 1
pyr_soma.pt3d = [(0.0, 0.0, 0.0, 20.0), (0.0, 0.0, 20.0, 20.0)]
pyr_bdend = ms.section("Bdend", "Bdend")
pyr_bdend.nseg = 1
pyr_bdend.pt3d = [(0.0, 0.0, 0.0, 2.0), (0.0, 0.0, -200.0, 2.0)]
pyr_adend1 = ms.section("Adend1", "Adend1")
pyr_adend1.nseg = 1
pyr_adend1.pt3d = [(0.0, 0.0, 20.0, 2.0), (0.0, 0.0, 170.0, 2.0)]
pyr_adend2 = ms.section("Adend2", "Adend2")
pyr_adend2.nseg = 1
pyr_adend2.pt3d = [(0.0, 0.0, 170.0, 2.0), (0.0, 0.0, 320.0, 2.0)]
pyr_adend3 = ms.section("Adend3", "Adend3")
pyr_adend3.nseg = 1
pyr_adend3.pt3d = [(0.0, 0.0, 320.0, 2.0), (0.0, 0.0, 470.0, 2.0)]
pyr_bdend.connect(pyr_soma, 0.0)
pyr_adend1.connect(pyr_soma, 0.5)
pyr_adend2.connect(pyr_adend1, 1.0)
pyr_adend3.connect(pyr_adend2, 1.0)
pyr_sections = [pyr_soma, pyr_bdend, pyr_adend1, pyr_adend2, pyr_adend3]

interneuron_area_um2 = 10000.0
interneuron_diam = math.sqrt(interneuron_area_um2)
interneuron_length = interneuron_diam / math.pi
bas_soma = ms.section("soma", "soma")
bas_soma.nseg = 1
bas_soma.pt3d = [
    (0.0, 0.0, 0.0, interneuron_diam),
    (0.0, 0.0, interneuron_length, interneuron_diam),
]
olm_soma = ms.section("soma", "soma")
olm_soma.nseg = 1
olm_soma.pt3d = [
    (0.0, 0.0, 0.0, interneuron_diam),
    (0.0, 0.0, interneuron_length, interneuron_diam),
]
micro.build_morphology(
    [
        {"name": "PYR", "num_cells": PYR_COUNT, "sections": pyr_sections},
        {"name": "BAS", "num_cells": BAS_COUNT, "sections": [bas_soma]},
        {"name": "OLM", "num_cells": OLM_COUNT, "sections": [olm_soma]},
    ]
)

pyr_population = micro.population("PYR")
bas_population = micro.population("BAS")
olm_population = micro.population("OLM")

for cell in pyr_population:
    cell.v_init = -65.0
    for label in ("soma", "Bdend", "Adend1", "Adend2", "Adend3"):
        group = cell.group(label)
        group.Ra = 150.0
        group.cm = 1.0
        group.insert("kdrcurrent")

    cell.group("soma").insert("pas", e=-70.0, g=0.0000357)
    cell.group("soma").insert("nacurrent")
    cell.group("soma").insert("kacurrent")
    cell.group("soma").insert("hcurrent")

    cell.group("Bdend").insert("pas", e=-70.0, g=0.0000357)
    cell.group("Bdend").insert("nacurrent", ki=1.0)
    cell.group("Bdend").insert("kacurrent")
    cell.group("Bdend").insert("hcurrent")

    cell.group("Adend1").insert("pas", e=-70.0, g=0.0000357)
    cell.group("Adend1").insert("nacurrent", ki=0.5)
    cell.group("Adend1").insert("kacurrent", g=0.072)
    cell.group("Adend1").insert("hcurrent", v50=-82.0, g=0.0002)

    cell.group("Adend2").insert("pas", e=-70.0, g=0.0000357)
    cell.group("Adend2").insert("nacurrent", ki=0.5)
    cell.group("Adend2").insert("kacurrent", g=0.0, gd=0.120)
    cell.group("Adend2").insert("hcurrent", v50=-90.0, g=0.0004)

    cell.group("Adend3").cm = 2.0
    cell.group("Adend3").insert("pas", e=-70.0, g=0.0000714)
    cell.group("Adend3").insert("nacurrent", ki=0.5)
    cell.group("Adend3").insert("kacurrent", g=0.0, gd=0.200)
    cell.group("Adend3").insert("hcurrent", v50=-90.0, g=0.0007)
    cell.group("soma")[0](0.5).insert("IClamp", **{"del": 0.2, "dur": 1.0e9, "amp": 0.1})
    soma = cell.group("soma")[0](0.5)
    sid = int(cell.gid)
    micro.network().register_spike_source(sid, soma._ref_v, SPIKE_THRESHOLD_MV)
for cell in bas_population:
    cell.v_init = -65.0
    soma = cell.group("soma")
    soma.Ra = 35.4
    soma.cm = 1.0
    soma.insert("pas", e=-65.0, g=0.1e-3)
    soma.insert("Nafbwb")
    soma.insert("Kdrbwb")
    sid = int(cell.gid)
    micro.network().register_spike_source(sid, soma[0](0.5)._ref_v, SPIKE_THRESHOLD_MV)
for cell in olm_population:
    cell.v_init = -65.0
    soma = cell.group("soma")
    soma.Ra = 35.4
    soma.cm = 1.0
    soma.insert("pas", e=-65.0, g=0.1e-3)
    soma.insert("Nafbwb")
    soma.insert("Kdrbwb")
    soma.insert("Iholmw")
    soma.insert("Caolmw")
    soma.insert("ICaolmw")
    soma.insert("KCaolmw")
    soma[0](0.5).insert("IClamp", **{"del": 0.2, "dur": 1.0e9, "amp": -25e-3})
    sid = int(cell.gid)
    micro.network().register_spike_source(sid, soma[0](0.5)._ref_v, SPIKE_THRESHOLD_MV)
```

Voltage locations that can emit spikes are registered as spike sources while each population is configured. Although this example uses `sid = int(cell.gid)` in `register_spike_source(sid, ref, threshold)`, the two are different concepts: `cell.gid` identifies a cell, while `sid` identifies a registered spike source. This example uses the same value only because each cell contributes one spike source.

```py
# Micro recurrent connections
conn_rng = random.Random(4321)

for cell in bas_population:
    target = cell.group("soma")[0](0.5).insert(
        "MyExp2SynNMDABB",
        tau1=0.05,
        tau2=5.3,
        tau1NMDA=15.0,
        tau2NMDA=150.0,
        r=1.0,
        e=0.0,
    )
    for pyr_local in conn_rng.sample(range(PYR_COUNT), 100):
        micro.network().sid_connect(int(pyr_population.gid_begin) + int(pyr_local), target, 1.15 * 1.2e-3, 2.0)

for cell in olm_population:
    target = cell.group("soma")[0](0.5).insert(
        "MyExp2SynNMDABB",
        tau1=0.05,
        tau2=5.3,
        tau1NMDA=15.0,
        tau2NMDA=150.0,
        r=1.0,
        e=0.0,
    )
    for pyr_local in conn_rng.sample(range(PYR_COUNT), 10):
        micro.network().sid_connect(int(pyr_population.gid_begin) + int(pyr_local), target, 0.7e-3, 2.0)

for cell in pyr_population:
    pyr_local_post = int(cell.gid) - int(pyr_population.gid_begin)
    target = cell.group("Bdend")[0](1.0).insert(
        "MyExp2SynNMDABB",
        tau1=0.05,
        tau2=5.3,
        tau1NMDA=15.0,
        tau2NMDA=150.0,
        r=1.0,
        e=0.0,
    )
    for pyr_local_pre in conn_rng.sample(range(PYR_COUNT), 25):
        if pyr_local_pre == pyr_local_post:
            continue
        micro.network().sid_connect(int(pyr_population.gid_begin) + int(pyr_local_pre), target, 0.004e-3, 2.0)

for cell in bas_population:
    target = cell.group("soma")[0](0.5).insert("MyExp2SynBB", tau1=0.05, tau2=5.3, e=0.0)
    for pyr_local in conn_rng.sample(range(PYR_COUNT), 100):
        micro.network().sid_connect(int(pyr_population.gid_begin) + int(pyr_local), target, 0.3 * 1.2e-3, 2.0)

for cell in olm_population:
    target = cell.group("soma")[0](0.5).insert("MyExp2SynBB", tau1=0.05, tau2=5.3, e=0.0)
    for pyr_local in conn_rng.sample(range(PYR_COUNT), 10):
        micro.network().sid_connect(int(pyr_population.gid_begin) + int(pyr_local), target, 0.3 * 1.2e-3, 2.0)

for cell in pyr_population:
    pyr_local_post = int(cell.gid) - int(pyr_population.gid_begin)
    target = cell.group("Bdend")[0](1.0).insert("MyExp2SynBB", tau1=0.05, tau2=5.3, e=0.0)
    for pyr_local_pre in conn_rng.sample(range(PYR_COUNT), 25):
        if pyr_local_pre == pyr_local_post:
            continue
        micro.network().sid_connect(int(pyr_population.gid_begin) + int(pyr_local_pre), target, 0.5 * 0.04e-3, 2.0)

for cell in bas_population:
    bas_local_post = int(cell.gid) - int(bas_population.gid_begin)
    target = cell.group("soma")[0](0.5).insert("MyExp2SynBB", tau1=0.07, tau2=9.1, e=-80.0)
    for bas_local_pre in conn_rng.sample(range(BAS_COUNT), 60):
        if bas_local_pre == bas_local_post:
            continue
        micro.network().sid_connect(int(bas_population.gid_begin) + int(bas_local_pre), target, 3.0 * 1.5e-3, 2.0)

for cell in pyr_population:
    target = cell.group("soma")[0](0.5).insert("MyExp2SynBB", tau1=0.07, tau2=9.1, e=-80.0)
    for bas_local in conn_rng.sample(range(BAS_COUNT), 50):
        micro.network().sid_connect(int(bas_population.gid_begin) + int(bas_local), target, 4.0 * 0.18e-3, 2.0)

for cell in olm_population:
    target = cell.group("soma")[0](0.5).insert("MyExp2SynBB", tau1=0.07, tau2=9.1, e=-80.0)
    for bas_local in conn_rng.sample(range(BAS_COUNT), 17):
        micro.network().sid_connect(int(bas_population.gid_begin) + int(bas_local), target, 0.05 * 4.0 * 0.18e-3, 2.0)

for cell in pyr_population:
    target = cell.group("Adend2")[0](0.5).insert("MyExp2SynBB", tau1=0.2, tau2=20.0, e=-80.0)
    for olm_local in conn_rng.sample(range(OLM_COUNT), 10):
        micro.network().sid_connect(int(olm_population.gid_begin) + int(olm_local), target, 0.08 * 4.0 * 3.0 * 6.0e-3, 2.0)
```

## Macro Modeling

MIND_Sim is designed as an extension of the [NEURON Simulator](https://neuron.yale.edu/neuron/). Therefore, the [MOD/NMODL](https://nrn.readthedocs.io/en/latest/nmodl/language/nmodl.html) language is used not only for ion channels and synapses, but also for macro-scale neural population dynamics, `macro2macro coupling`, `macro2micro transforms`, and `micro2macro transforms`.

The cross-scale transform design follows the event-based view used in recent multiscale co-simulation studies, including [Hater, Courson, Lu, Diaz-Pier, and Manos (2026), Arbor-TVB: a novel multi-scale co-simulation framework with a case study on neural-level seizure generation and whole-brain propagation](https://doi.org/10.3389/fncom.2025.1731161), and [Kusch, Diaz-Pier, Klijn, Sontheimer, Bernard, Morrison, and Jirsa (2024), Multiscale co-simulation design pattern for neuroscience applications](https://doi.org/10.3389/fninf.2024.1156683). From a NEURON perspective, `micro2macro transforms` are analogous to handling spike events emitted by individual cells, while `macro2micro transforms` are analogous to external NetStim-like event injection into selected micro-scale synapses. `macro2macro coupling` is also expressed as a connection rule: a source ROI exposes a variable, an edge-level rule transforms it through weight and delay, and the result contributes to a named input of the target ROI. Unlike synaptic events, this macro2macro path is continuous rather than spike-discrete.

At the macro level, the model remains connectome-based. ROI-to-ROI coupling does not need to know whether an ROI is implemented by a macro equation or by a microcircuit. The coupling interface is determined by the source ROI's `SOURCE_EXPOSURE` and the target ROI's `TARGET_INPUT`. This means that one microcircuit can cover multiple ROIs, and different ROIs can still use different neural mass or neural field models.

This role split also determines where coupling nonlinearities should be written. If a model first sums incoming edge contributions and then applies a nonlinear operation, that nonlinear operation belongs in the `ROLE REGION` mechanism, because the region mechanism receives the accumulated `TARGET_INPUT`. If a model applies a nonlinear operation to each edge before summation, that operation belongs in the `ROLE MACRO2MACRO` mechanism, because `MACRO2MACRO` is evaluated at the edge level before contributing to the target input.

The benefit of this design is that every ROI and every micro-scale neuron remains explicitly addressable. Different ROIs can use different macro equations and coupling rules, while individual neurons can still receive heterogeneous macro2micro inputs or contribute to different micro2macro outputs. Runtime efficiency is preserved by grouping mechanisms and variables by name in structure-of-arrays layouts, so heterogeneous model components can still be executed in batched form.

The transform mechanisms used in this demo are listed below. The ordinary `NEURON` blocks still describe MOD mechanisms, while the additional `MIND` blocks declare how each mechanism participates in the macro and cross-scale graph.

`tvb_epileptor2d.mod` defines the ROI-level Epileptor2D macro model.

```text
NEURON {
    POINT_PROCESS tvb_epileptor2d
    RANGE coupled_x, x, z
    RANGE x0, a, b, c, d, r, slope, kvf, ks, tt, i_ext, modification
}

MIND {
    ROLE REGION
    TARGET_INPUT coupled_x
    SOURCE_EXPOSURE x, z
}

PARAMETER {
    x0 = -2.4
    a = 1.0
    b = 3.0
    c = 1.0
    d = 5.0
    r = 0.00035
    slope = 0.0
    kvf = 0.35
    ks = 0.0
    tt = 1.0
    i_ext = 3.1
    modification = 0.0
}

ASSIGNED {
    coupled_x
}

STATE {
    x
    z
}

INITIAL {
    x = 0.0
    z = 0.0
}

BREAKPOINT {
    SOLVE states METHOD euler
}

DERIVATIVE states {
    LOCAL fast_term, z_minus, slow_term, h_term

    fast_term = a * x * x + (d - b) * x
    if (x >= 0.0) {
        z_minus = z - 4.0
        fast_term = -slope - 0.6 * z_minus * z_minus + d * x
    }

    slow_term = 0.0
    if (z < 0.0) {
        slow_term = -0.1 * z ^ 7
    }

    h_term = 4.0 * (x - x0) + slow_term
    if (modification > 0.5) {
        h_term = x0 + 3.0 / (1.0 + exp(-(x + 0.5) / 0.1))
    }

    x' = tt * (c - z + i_ext + kvf * coupled_x - fast_term * x)
    z' = tt * r * (h_term - z + ks * coupled_x)
}
```

`vep_x_macro2macro.mod` maps a source ROI's `x` exposure into the `coupled_x` input of another macro ROI.

```text
NEURON {
    POINT_PROCESS vep_x_macro2macro
    RANGE x, coupled_x, weight, delay, a
}

MIND {
    ROLE MACRO2MACRO
    SOURCE_EXPOSURE x
    TARGET_INPUT coupled_x
}

PARAMETER {
    a = 1.0
}

ASSIGNED {
    x
    coupled_x
    weight
    delay
}

BREAKPOINT {
    coupled_x = coupled_x + a * weight * x
}
```

`ca3_input_macro2macro.mod` maps macro inputs into the `ca3_input` variable used by the CA3 macro2micro transform.

```text
NEURON {
    POINT_PROCESS ca3_input_macro2macro
    RANGE x, ca3_input, weight, delay, a
}

MIND {
    ROLE MACRO2MACRO
    SOURCE_EXPOSURE x
    TARGET_INPUT ca3_input
}

PARAMETER {
    a = 1.0
}

ASSIGNED {
    x
    ca3_input
    weight
    delay
}

BREAKPOINT {
    ca3_input = ca3_input + a * weight * x
}
```

`ca3_input_to_spikes.mod` converts the macro `ca3_input` variable into generated spike events.

```text
NEURON {
    ARTIFICIAL_CELL ca3_input_to_spikes
    THREADSAFE
    RANGE ca3_input, rate, start_time, stop_time
    RANGE base_hz, gain_hz, max_rate_hz, threshold, slope
    RANDOM rng
}

MIND {
    ROLE MACRO2MICRO
    TARGET_INPUT ca3_input
}

PARAMETER {
    base_hz = 1.0
    gain_hz = 45.0
    max_rate_hz = 120.0
    threshold = -0.35
    slope = 4.0
}

ASSIGNED {
    ca3_input
    rate
    start_time
    stop_time
    window_ms
    lambda
    spike_count
    count
    event_time
}

PROCEDURE update_rate() {
    rate = base_hz + gain_hz / (1.0 + exp(-slope * (ca3_input - threshold)))
    if (rate > max_rate_hz) {
        rate = max_rate_hz
    }
    if (rate < 0.0) {
        rate = 0.0
    }
}

FUNCTION poisson_count(mean) {
    LOCAL limit, product
    poisson_count = 0.0
    if (mean > 0.0) {
        limit = exp(-mean)
        product = 1.0
        poisson_count = -1.0
        while (product > limit) {
            poisson_count = poisson_count + 1.0
            product = product * random_uniform(rng)
        }
    }
}

NET_RECEIVE(weight) {
    if (flag == 0.0) {
        update_rate()
        if (rate > 0.0) {
            window_ms = stop_time - t
            lambda = rate * window_ms / 1000.0
            spike_count = poisson_count(lambda)
            count = 0.0
            while (count < spike_count) {
                event_time = t + window_ms * random_uniform(rng)
                net_send(event_time - t, 1.0)
                count = count + 1.0
            }
        }
    }
    if (flag == 1.0) {
        net_event(t)
    }
}
```

The micro2macro path is split into one transform per source population. `ca3_pyr_spikes_to_vep.mod` converts pyramidal cell spikes into a positive contribution to the macro `x` exposure.

```text
NEURON {
    POINT_PROCESS ca3_pyr_spikes_to_vep
    RANGE x
    RANGE activity
    RANGE tau_ms, x_baseline, gain, population_size
}

MIND {
    ROLE MICRO2MACRO
    SOURCE_EXPOSURE x
}

PARAMETER {
    tau_ms = 50.0
    x_baseline = -1.8
    gain = 2.0
    population_size = 800.0
}

ASSIGNED {
    x
}

STATE {
    activity
}

INITIAL {
    activity = 0.0
}

BREAKPOINT {
    SOLVE states METHOD cnexp
    x = x_baseline + gain * activity
}

DERIVATIVE states {
    activity' = -activity / tau_ms
}

NET_RECEIVE(weight) {
    activity = activity + weight / population_size
}
```

`ca3_bas_spikes_to_vep.mod` converts basket cell spikes into an inhibitory contribution.

```text
NEURON {
    POINT_PROCESS ca3_bas_spikes_to_vep
    RANGE x
    RANGE activity
    RANGE tau_ms, gain, population_size
}

MIND {
    ROLE MICRO2MACRO
    SOURCE_EXPOSURE x
}

PARAMETER {
    tau_ms = 20.0
    gain = -0.7
    population_size = 200.0
}

ASSIGNED {
    x
}

STATE {
    activity
}

INITIAL {
    activity = 0.0
}

BREAKPOINT {
    SOLVE states METHOD cnexp
    x = gain * activity
}

DERIVATIVE states {
    activity' = -activity / tau_ms
}

NET_RECEIVE(weight) {
    activity = activity + weight / population_size
}
```

`ca3_olm_spikes_to_vep.mod` converts OLM cell spikes into a second inhibitory contribution.

```text
NEURON {
    POINT_PROCESS ca3_olm_spikes_to_vep
    RANGE x
    RANGE activity
    RANGE tau_ms, gain, population_size
}

MIND {
    ROLE MICRO2MACRO
    SOURCE_EXPOSURE x
}

PARAMETER {
    tau_ms = 80.0
    gain = -0.4
    population_size = 200.0
}

ASSIGNED {
    x
}

STATE {
    activity
}

INITIAL {
    activity = 0.0
}

BREAKPOINT {
    SOLVE states METHOD cnexp
    x = gain * activity
}

DERIVATIVE states {
    activity' = -activity / tau_ms
}

NET_RECEIVE(weight) {
    activity = activity + weight / population_size
}
```

At the macro scale, ROIs other than `Left-CA3` use the `tvb_epileptor2d` mechanism. `Left-CA3` is marked as a micro ROI, so its regional behavior is supplied through the CA3 microcircuit and the transform modules.

```py
macro_rng = np.random.default_rng(1234)
propagation_labels = {
    "Left-CA1",
    "Right-CA1",
    "Left-CA3",
    "Right-CA3",
    "Left-subiculum",
    "Right-subiculum",
    "Left-entorhinal",
    "Right-entorhinal",
}
for roi in rois.rois():
    if roi.label == left_ca3_roi.label:
        x0 = -1.6
    elif roi.label in propagation_labels:
        x0 = -1.9
    else:
        x0 = -2.4
    initial_state = {"x": x0 + 0.02 * float(macro_rng.standard_normal()), "z": 0.0}
    if roi.label != left_ca3_roi.label:
        roi.use_macro(
            "tvb_epileptor2d",
            initial_state=initial_state,
            params={
                "x0": x0,
                "a": 1.0,
                "b": 3.0,
                "c": 1.0,
                "d": 5.0,
                "r": 0.00035,
                "slope": 0.0,
                "kvf": 0.35,
                "ks": 0.0,
                "tt": 1.0,
                "i_ext": 3.1,
                "modification": 0.0,
            },
        )

left_ca3_roi.use_micro()
```

The `macro2micro transform` converts the `ca3_input` signal into spike events delivered to synapses on CA3 pyramidal cells.

```py
ca3_input_to_spikes_params = {
    "base_hz": 1.0,
    "gain_hz": 45.0,
    "max_rate_hz": 120.0,
    "threshold": -0.35,
    "slope": 4.0,
}
for cell in pyr_population:
    target = cell.group("Adend3")[0](0.5).insert("MyExp2SynBB", tau1=0.05, tau2=5.3, e=0.0)
    left_ca3_roi.macro2micro(
        "ca3_input_to_spikes",
        target=target,
        weight=0.02e-3 * 1.0e-2,
        delay=0.2,
        params=ca3_input_to_spikes_params,
    )
```

The same `mod/` directory contains the extended MOD mechanisms used by the macro layer and by the cross-scale transforms. `tvb_epileptor2d` defines the ROI-level neural mass. `vep_x_macro2macro` propagates the `x` exposure between macro ROIs. For the micro ROI, `ca3_input_macro2macro` collects incoming macro activity into the `ca3_input` variable.

```py
for target in rois.rois():
    if target.label == left_ca3_roi.label:
        for source in rois.rois():
            target.insert(
                source.label,
                "ca3_input_macro2macro",
            )
        continue
    for source in rois.rois():
        target.insert(
            source.label,
            "vep_x_macro2macro",
        )
```

The `micro2macro transform` maps spikes from pyramidal, basket, and OLM cells into the `x` exposure of the `Left-CA3` ROI. Source selection is defined by explicit `sid` values. Multiple `micro2macro transforms` can target the same ROI and exposure.

```py
ca3_pyr_spikes_to_vep_params = {
    "tau_ms": 50.0,
    "x_baseline": -1.8,
    "gain": 2.0,
    "population_size": 800.0,
}
ca3_bas_spikes_to_vep_params = {
    "tau_ms": 20.0,
    "gain": -0.7,
    "population_size": 200.0,
}
ca3_olm_spikes_to_vep_params = {
    "tau_ms": 80.0,
    "gain": -0.4,
    "population_size": 200.0,
}
for cell in pyr_population:
    left_ca3_roi.micro2macro(
        "ca3_pyr_spikes_to_vep",
        sid=int(cell.gid),
        params=ca3_pyr_spikes_to_vep_params,
    )
for cell in bas_population:
    left_ca3_roi.micro2macro(
        "ca3_bas_spikes_to_vep",
        sid=int(cell.gid),
        params=ca3_bas_spikes_to_vep_params,
    )
for cell in olm_population:
    left_ca3_roi.micro2macro(
        "ca3_olm_spikes_to_vep",
        sid=int(cell.gid),
        params=ca3_olm_spikes_to_vep_params,
    )

micro.build_microcircuit()
```

## Recording

At the macro level, recording is matched exactly by exposure name.

```py
for roi in rois.rois():
    roi.record("x")
    roi.record("z")
```

At the micro level, recording follows the familiar NEURON Simulator-like style.

```py
pyr_voltage_trace = ms.Vector().record(pyr_population[0].group("soma")[0](0.5)._ref_v)
bas_voltage_trace = ms.Vector().record(bas_population[0].group("soma")[0](0.5)._ref_v)
olm_voltage_trace = ms.Vector().record(olm_population[0].group("soma")[0](0.5)._ref_v)
adend3_voltage_trace = ms.Vector().record(pyr_population[0].group("Adend3")[0](0.5)._ref_v)
voltage_time_trace = ms.Vector().record(micro._ref_t)
```

After recording is configured, the model can be executed.

```py
micro.finitialize(-65.0)
simulator = ms.Simulator(rois)
result = simulator.run(float(args.duration_ms))
```

## Performance

In this example, MIND_Sim is compared with a TVB+NEURON reference using the current 1 s CA3 epilepsy co-simulation runs.

| Workflow | Threads | Pre-run | Run | Speedup |
| --- | ---: | ---: | ---: | ---: |
| MIND_Sim async | 1 | 0.274s | 14.940s | 3.68x |
| MIND_Sim async | 4 | 0.289s | 5.844s | 4.80x |
| TVB+NEURON | 1 | 1.443s | 54.967s | 1.00x |
| TVB+NEURON | 4 | 1.423s | 28.041s | 1.00x |

For the same 1 s runs, the maximum absolute differences between MIND_Sim and the TVB+NEURON reference are `1.09e-14` for macro `x`, `3.56e-14` for macro `z`, and less than `9e-11 mV` for representative PYR, BAS, OLM, and PYR Adend3 voltage traces. Spike sample indices are exactly equal for the representative PYR, BAS, and OLM cells. This result should be read as an example-level performance comparison, not as a standardized benchmark. The reference TVB+NEURON implementation is available [here](https://github.com/HengyeZhu/MIND_Sim/blob/main/examples/ca3_epilepsy_cosim/neuron_tvb/run_tvb_neuron_ca3_cosim.py).
