# Generate html documentation from source code
pdoc3 --force --html --config show_source_code=False gamelib -o docs

# post process -- remove unnecessary class prefix
sed -i 's/_GameThread\.//g' docs/gamelib.html > docs/index.html

# rename index file
mv -f docs/gamelib.html docs/index.html
