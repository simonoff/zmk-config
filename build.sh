python3 generate_keymap.py

west build -d build/left -s zmk/app -b nice_nano -- -DSHIELD=corne_left -DZMK_CONFIG="$(pwd)/config" || exit
west build -d build/right -s zmk/app -b nice_nano -- -DSHIELD=corne_right -DZMK_CONFIG="$(pwd)/config" || exit

cp build/left/zephyr/zmk.uf2 build/left.uf2
cp build/right/zephyr/zmk.uf2 build/right.uf2
