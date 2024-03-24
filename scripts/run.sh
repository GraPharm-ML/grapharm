# Fine-tuning ULTRA model
srun -J "ultra" -p gpu --qos=gpu --gres=gpu:1 --cpus-per-task=4 --mem=1000000 python script/run.py \
-c config/transductive/inference.yaml \
--dataset Hetionet --epochs 20 --bpe 1024 --gpus "[0]" \
--ckpt ~/DATA/zeus/hnguyent/projects/LEARNING/ULTRA/ckpts/ultra_50g.pth

# Transductive inference to uncover new links
srun -J "ultra" -p gpu --qos=gpu --gres=gpu:1 --cpus-per-task=4 --mem=1000000 python scripts/gen_new_links.py \
    -ckpt "ultra_50g.pth" \
    -dataset "Hetionet" \
    -gpus "[0]"

# Run inference on full dataset
srun -J "ultra" -p gpu --qos=gpu --gres=gpu:1 --cpus-per-task=4 --mem=1000000 python scripts/gen_new_links.py \
    -ckpt "ultra_50g.pth" \
    -dataset "HetionetA" \
    -gpus "[0]"

srun -J "ultra50-full" -p gpu --qos=gpu --gres=gpu:2 --cpus-per-task=4 --mem=1000000 python scripts/gen_new_links.py \
    -ckpt "ultra50g_hetionet50.pth" \
    -dataset "HetionetA" \
    -gpus "[0,1]"


srun -J "ultra50-test" -p gpu --qos=gpu --gres=gpu:1 --cpus-per-task=4 --mem=1000000 python scripts/gen_new_links.py \
    -ckpt "ultra50g_hetionet50.pth" \
    -dataset "Hetionet" \
    -gpus "[0]"


srun -J "ultra100-test" -p gpu --qos=gpu --gres=gpu:1 --cpus-per-task=4 --mem=500000 python scripts/gen_new_links.py \
    -ckpt "ultra50g_hetionet100.pth" \
    -dataset "Hetionet" \
    -gpus "[0]"

srun -J "ultra100-full" -p gpu --qos=gpu --gres=gpu:1 --cpus-per-task=4 --mem=500000 python scripts/gen_new_links.py \
    -ckpt "ultra50g_hetionet100.pth" \
    -dataset "HetionetA" \
    -gpus "[0]"

