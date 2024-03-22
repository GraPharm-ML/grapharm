#!/bin/bash
ENVNAME="grapharm-ml"

is_installed=$(conda info --envs | grep $ENVNAME -c)

if [[ "${is_installed}" == "0" ]];then
  conda create -n $ENVNAME python=3.9 -y;
fi

if [[ `command -v activate` ]]
then
  source `which activate` $ENVNAME
else
  conda activate $ENVNAME
fi

# Check to make sure grapharm is activated
if [[ "${CONDA_DEFAULT_ENV}" != $ENVNAME ]]
then
  echo "Could not run conda activate $ENVNAME, please check the errors";
  exit 1;
fi

#########
# ULTRA #
#########
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cu118
pip install torch-scatter==2.1.2 torch-sparse==0.6.18 torch-geometric==2.4.0 -f https://data.pyg.org/whl/torch-2.1.0+cu118.html
pip install ninja easydict pyyaml
conda install --channel conda-forge pygraphviz

torch_home_path="${TORCH_HOME}"

if [ "${torch_home_path}" ]
then
  conda env config vars set TORCH_HOME="${torch_home_path}"
fi

pip_exc="${CONDA_PREFIX}/bin/pip"

$pip_exc install -e . # For development

