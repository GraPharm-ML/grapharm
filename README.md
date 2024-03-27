<img src="./assets/Logo_hori@33.33x.png" alt="GraPharm"/>


<a href="https://colab.research.google.com/github/grapharm-ml/grapharm/blob/master/evaluation.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab" height=27/></a></a> <a href="https://grapharm-ml.github.io/" target="_parent"><img src="https://img.shields.io/badge/github%20pages-121013?style=for-the-badge&logo=github&logoColor=white" alt="Page" height=27/></a>

GraPharm aims to learn new biological links between diseases, compounds, genes, pathways, biological process, *etc.* to unveil the hidden biological relations, accelerating drug discovery.

## Prerequisites
To run the code in this respository, make sure you have installed Miniconda/Anaconda. Then, follow these steps to install the required packages:
* Download this repo: `git clone https://github.com/GraPharm-ML/grapharm`
* Change dir to `grapharm` folder.
* Install required packages inside virtual environment:  `bash install.sh`
* Later for new updates in the package: `pip install -e .`

## Uncovering new relations
* Inference on test data: `python scripts/gen_new_links.py -ckpt "ultra_50g.pth" -dataset "Hetionet" -gpus "[0]"`
* Add new links into the graph: `python scripts/add_new_links_to_graph.py -result_name "ultra_50g-Hetionet.csv" -savename "new_links_v0.csv"`

> Reference: [`ultra`](./ultra/) was adapted from [ULTRA](https://github.com/DeepGraphLearning/ULTRA) with some modifications.

## Notebooks
To add conda virlenv to Jupyter kernel, first activate the `grapharm` env then type: `python -m ipykernel install --user --name grapharm`

* [01_hetionet_analysis.ipynb](notebooks/01_hetionet_analysis.ipynb): Data analysis for Hetionet
* [02_ultra.ipynb](notebooks/03_ultra.ipynb): Analysis of the model result

## References
* [ULTRA: Towars Foundation Models for Knowledge Graph Reasoning](https://openreview.net/forum?id=jVEoydFOl9&referrer=%5Bthe%20profile%20of%20Mikhail%20Galkin%5D(%2Fprofile%3Fid%3D~Mikhail_Galkin1))
* [Hetionet - An integrative network of biomedical knowledge](https://het.io/)

## Acknowledgement
* Thank Totoro for very useful discussions about state-of-the-art methods for Graph Reasoning
