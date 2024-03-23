# On maestro
srun -J "ultra" -p gpu --qos=gpu --gres=gpu:1 --cpus-per-task=4 --mem=1000000 python scripts/gen_new_links.py \
    -ckpt "ultra_50g.pth" \
    -dataset "Hetionet" \
    -gpus "[0]"
