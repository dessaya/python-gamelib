pdoc3 --force --html --config show_source_code=False gamelib -o docs
sed s/_GameThread\.//g docs/gamelib.html > docs/index.html
rm -f docs/gamelib.html
