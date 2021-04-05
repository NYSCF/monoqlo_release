# Monoqlo
Monoqlo is a deep learning framework for automatically detecting and assessing the clonality of clonalized cell lines from daily imaging data. 

This repository implements an illustrative example of the Monoqlo framework. For full details on the design rationale and execution logic of Monoqlo, please see our preprint:
https://www.biorxiv.org/content/10.1101/2020.12.28.424610v1



![Data generation](data_generation.png)

Monoqlo serves as a useful tool in laboratory automation scenarios in which cells are monoclonalized and imaged, such as illustrated in the figure above.



# Installation

The Monoqlo framework itself does not require installation other than downloading this repository, but has various requirements and dependencies which must be installed (see below)

# Recommended Hardware

- CUDA-capable GPU (NVIDIA RTX 2080 Ti / 3080 Ti or similar)
  - (The framework can be executed on a CPU, but will benefit hugely from GPU acceleration due to the large number of images that must be analyzed.)
- 16GB+ memory
- High-end CPU (Intel Core i9-9900k or similar)


# Software Requirements and Dependencies

Note - the software versions indicated here are those that were uesd during testing. Other versions may work, however we cannot guarantee there will not be compatibility issues.
Note - it is highly advised to use an environment manager (e.g. Anaconda) when installing these software and dependencies.

